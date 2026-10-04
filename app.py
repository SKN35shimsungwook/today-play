"""오늘 뭐하고 놀래? 🍻 — 친구랑 놀 코스를 레트로 메뉴판에서 주문하는 Streamlit 앱."""

import datetime as dt
import random
from html import escape

import streamlit as st

from menu import (
    CAFE_CONCEPTS,
    CAFE_DRINKS,
    COURSE_TYPES,
    DRINK,
    EXCUSES,
    HOME_TEASES,
    HOME_TIMES,
    JOKE_PRICES,
    LATER_LADDER,
    MEAL,
    MEET_TIMES,
    NO_TAKEBACK,
    PAY_WAYS,
    PLAY,
)

st.set_page_config(page_title="오늘 뭐하고 놀래?", page_icon="🍻", layout="centered")

KST = dt.timezone(dt.timedelta(hours=9))
CUSTOM_TIME = "⏰ 직접 정하기"
MAX_COURSE = 8

# ---------------------------------------------------------------------------
# 상태
# ---------------------------------------------------------------------------
ss = st.session_state

# "p_"로 시작하는 key = 친구가 고른 값. 페이지를 넘겨도 지워지지 않도록 매 실행마다 다시 대입한다.
for _k in [k for k in ss.keys() if str(k).startswith("p_")]:
    ss[_k] = ss[_k]

DEFAULTS = {
    "step": 0,
    "excuse_mode": False,
    "rejected": [],
    "course": [],
    "home": None,  # 최종 귀가 시간
    "home_wanted": None,  # 원래 가고 싶었던 (기각된) 시간
    "home_msg": "",
    "home_score": -1,  # 얼마나 늦게 가는지 (클수록 늦게)
    "p_people": 2,
    "p_meet": MEET_TIMES[1],
    "p_meet_custom": dt.time(19, 0),
    "p_home_custom": dt.time(23, 0),
    "p_budget": 3,
    "p_pay": PAY_WAYS[0],
}
for _k, _v in DEFAULTS.items():
    ss.setdefault(_k, list(_v) if isinstance(_v, list) else _v)


def steps() -> list[str]:
    return ["intro", "info", "course"] + [f"menu:{i}" for i in range(len(ss.course))] + ["budget", "receipt"]


def go(step: int) -> None:
    ss.step = max(0, min(step, len(steps()) - 1))


def restart() -> None:
    for k in list(ss.keys()):
        del ss[k]


# ---------------------------------------------------------------------------
# 전역 스타일: 레트로 메뉴판
# ---------------------------------------------------------------------------
st.html(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&family=Gowun+Dodum&family=Nanum+Gothic+Coding:wght@400;700&display=swap');

:root {
  --paper: #fdf6e3; --card: #fffaf0; --ink: #3b2f2a; --red: #c0392b; --muted: #8a7563;
}
.stApp {
  background-color: var(--paper);
  background-image:
    radial-gradient(rgba(59,47,42,.06) 1px, transparent 1px),
    radial-gradient(rgba(59,47,42,.04) 1px, transparent 1px);
  background-size: 22px 22px, 13px 13px;
  background-position: 0 0, 7px 9px;
  color: var(--ink);
}
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea {
  font-family: 'Gowun Dodum', sans-serif;
}
h1, h2, h3 {
  font-family: 'Nanum Pen Script', cursive !important;
  color: var(--ink) !important; text-align: center !important; letter-spacing: 1px;
}
h1 { font-size: clamp(2.6rem, 11vw, 3.6rem) !important; }
h2 { font-size: clamp(2rem, 8vw, 2.6rem) !important; }

/* 테두리 박스: st.container(key="card_*") */
[class*="st-key-card_"] {
  background: var(--card);
  border: 2px solid var(--ink) !important;
  border-radius: 6px !important;
  box-shadow: 4px 4px 0 var(--ink);
}

.stButton button, .stDownloadButton button {
  font-family: 'Gowun Dodum', sans-serif !important;
  background: var(--card) !important; color: var(--ink) !important;
  border: 2px solid var(--ink) !important; border-radius: 6px !important;
  box-shadow: 3px 3px 0 var(--ink); transition: transform .08s, box-shadow .08s;
}
.stButton button:hover { transform: translate(-1px, -1px); box-shadow: 4px 4px 0 var(--ink); }
.stButton button:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--ink); }
.stButton button[kind="primary"] { background: var(--red) !important; color: #fff !important; }
.stButton button:disabled { opacity: .45; box-shadow: none; }

.stTabs [data-baseweb="tab"] { font-family: 'Gowun Dodum', sans-serif; }

.eyebrow { text-align: center; color: var(--muted); letter-spacing: .35em; font-size: .85rem; }
.stApp .hand { font-family: 'Nanum Pen Script', cursive; font-size: 1.7rem; text-align: center; }
.chain { text-align: center; font-size: 1.15rem; line-height: 2.2; }
.chain .tag {
  display: inline-block; border: 2px solid var(--ink); border-radius: 4px;
  padding: 0 .5em; background: #fff; margin: 0 .15em;
}
.chain .arrow { color: var(--muted); }

.excuse { display: flex; align-items: center; gap: .6rem; margin: .35rem 0; flex-wrap: wrap; }
.excuse s { color: var(--muted); }
.excuse .reply { color: var(--ink); font-size: .95rem; width: 100%; padding-left: .2rem; }
.stamp {
  display: inline-block; color: var(--red); border: 3px solid var(--red); border-radius: 6px;
  padding: 0 .45em; font-family: 'Nanum Pen Script', cursive; font-size: 1.5rem;
  transform: rotate(-8deg); opacity: .9;
}

.receipt {
  font-family: 'Nanum Gothic Coding', monospace; background: #fff; color: #222;
  max-width: 380px; margin: 0 auto; padding: 22px 20px 26px;
  box-shadow: 0 6px 18px rgba(0,0,0,.12);
  -webkit-mask: radial-gradient(circle 6px at 50% 100%, transparent 98%, #000) 50% 100% / 14px 100% repeat-x;
          mask: radial-gradient(circle 6px at 50% 100%, transparent 98%, #000) 50% 100% / 14px 100% repeat-x;
}
.receipt h3 { font-family: 'Nanum Gothic Coding', monospace !important; font-size: 1.25rem; margin: 0; }
.receipt .center { text-align: center; }
.receipt .small { font-size: .8rem; color: #666; }
.receipt hr { border: none; border-top: 2px dashed #999; margin: 10px 0; }
.receipt .row { display: flex; gap: 6px; font-size: .92rem; margin: 3px 0; }
.receipt .row .fill { flex: 1; border-bottom: 2px dotted #bbb; transform: translateY(-5px); }
.receipt .row .price { color: #777; white-space: nowrap; }
.receipt .sec { font-weight: 700; margin-top: 8px; }
.receipt .sub { font-size: .82rem; color: #555; margin-top: 4px; }
.receipt .total { display: flex; justify-content: space-between; font-weight: 700; font-size: 1.05rem; }
.receipt .barcode {
  height: 38px; margin-top: 12px;
  background: repeating-linear-gradient(90deg, #222 0 2px, transparent 2px 4px, #222 4px 7px, transparent 7px 9px, #222 9px 10px, transparent 10px 13px);
}
</style>
"""
)


def header() -> None:
    names = steps()
    st.html(f'<div class="eyebrow">— STEP {ss.step + 1} / {len(names)} —</div>')


def nav(next_disabled: bool = False, next_label: str = "다음 →") -> None:
    left, right = st.columns(2)
    left.button("← 이전", on_click=go, args=(ss.step - 1,), width="stretch")
    right.button(next_label, on_click=go, args=(ss.step + 1,), type="primary", disabled=next_disabled, width="stretch")


# ---------------------------------------------------------------------------
# 직접 입력 공용
# ---------------------------------------------------------------------------
def add_custom(input_key: str, list_key: str, target_key: str, multi: bool) -> None:
    text = ss[input_key].strip()
    if not text:
        return
    item = f"✏️ {text}"
    if item not in ss[list_key]:
        ss[list_key] = ss[list_key] + [item]
    if multi:
        if item not in ss[target_key]:
            ss[target_key] = ss[target_key] + [item]
    else:
        ss[target_key] = item
    ss[input_key] = ""


def custom_input(label: str, placeholder: str, input_key: str, list_key: str, target_key: str, multi: bool) -> None:
    args = (input_key, list_key, target_key, multi)
    left, right = st.columns([3, 1], vertical_alignment="bottom")
    # 엔터만 쳐도 추가되도록 on_change에도 연결
    left.text_input(label, placeholder=placeholder, max_chars=20, key=input_key, on_change=add_custom, args=args)
    right.button("추가", key=f"{input_key}_btn", on_click=add_custom, args=args, width="stretch")


# ---------------------------------------------------------------------------
# ① 첫 화면: 핑계 대기
# ---------------------------------------------------------------------------
def reject(excuse: str) -> None:
    ss.rejected = ss.rejected + [excuse]


def page_intro() -> None:
    st.html('<div class="eyebrow">— TODAY\'S MENU —</div>')
    st.markdown("# 오늘 뭐하고 놀래? 🍻")
    with st.container(border=True, key="card_0"):
        st.html('<p class="hand">오늘 놀 사람? 🙋</p>')
        if not ss.excuse_mode:
            left, right = st.columns(2)
            left.button("콜! 🍻", on_click=go, args=(1,), type="primary", width="stretch")
            if right.button("핑계 대기 😩", width="stretch"):
                ss.excuse_mode = True
                st.rerun()
            return

        remaining = [e for e in EXCUSES if e not in ss.rejected]
        for excuse in ss.rejected:
            st.html(
                f'<div class="excuse"><s>{escape(excuse)}</s> <span class="stamp">기각</span>'
                f'<span class="reply">↳ {escape(EXCUSES[excuse])}</span></div>'
            )
        if remaining:
            st.caption(f"핑계 골라봐. 하나씩 다 기각해줄게 😏 (남은 핑계 {len(remaining)}개)")
            cols = st.columns(2)
            for i, excuse in enumerate(remaining):
                cols[i % 2].button(excuse, key=f"excuse_{excuse}", on_click=reject, args=(excuse,), width="stretch")
            st.button("그냥 놀래 🍻", on_click=go, args=(1,), type="primary", width="stretch")
        else:
            st.html('<p class="hand">핑계 다 떨어졌지? 😎</p>')
            st.button("...알았어 놀자 🥲", on_click=go, args=(1,), type="primary", width="stretch")


# ---------------------------------------------------------------------------
# ② 기본 정보 + 집 가는 시간
# ---------------------------------------------------------------------------
def is_early(hour: int) -> bool:
    return 6 <= hour < 23


def hour_label(h: int, m: int) -> str:
    ampm = "새벽" if h < 6 else "오전" if h < 12 else "오후" if h < 18 else "밤"
    return f"{ampm} {h % 12 or 12}시" + (f" {m}분" if m else "")


def lateness(hour: int, minute: int) -> int:
    """저녁 6시부터 몇 분 지났는지. 새벽은 다음날로 친다."""
    return (hour * 60 + minute - 18 * 60) % (24 * 60)


def choose_home(label: str, hour: int, minute: int = 0) -> None:
    plain = label.split(" ", 1)[-1] if label.startswith(("🏠", "🌙", "🚇", "🌅")) else label
    if is_early(hour):
        # 일찍 가려고 할수록 한 칸씩 더 늦어진다 (지금보다 이른 칸은 건너뜀)
        ladder = [x for x in LATER_LADDER if lateness(x[1], x[2]) > ss.home_score] or LATER_LADDER[-1:]
        new_label, h, m = ladder[0]
        ss.home, ss.home_score, ss.home_wanted = new_label, lateness(h, m), label
        ss.home_msg = random.choice(HOME_TEASES).format(t=plain)
    elif lateness(hour, minute) < ss.home_score:
        ss.home_wanted = label
        ss.home_msg = NO_TAKEBACK.format(t=ss.home)
    else:
        ss.home, ss.home_score, ss.home_wanted = label, lateness(hour, minute), None
        ss.home_msg = "오~ 좀 아는데? 😏"


def choose_custom_home() -> None:
    t = ss.p_home_custom
    choose_home(hour_label(t.hour, t.minute), t.hour, t.minute)


def use_custom_meet() -> None:
    ss.p_meet = CUSTOM_TIME


def page_info() -> None:
    header()
    st.markdown("## 📋 기본 정보")
    with st.container(border=True, key="card_1"):
        st.number_input("몇 명이서?", min_value=2, max_value=20, step=1, key="p_people")

        st.radio("몇 시에 볼까?", MEET_TIMES + [CUSTOM_TIME], horizontal=True, key="p_meet")
        # 항상 보이게: 시간을 바꾸면 자동으로 '직접 정하기'가 선택된다
        st.time_input(
            "⏰ 직접 정하기 (바꾸면 이 시간으로)",
            step=dt.timedelta(minutes=10),
            key="p_meet_custom",
            on_change=use_custom_meet,
        )

    with st.container(border=True, key="card_2"):
        st.html('<p class="hand">🏠 집에는 몇 시에 갈 거야?</p>')
        cols = st.columns(3)
        for i, (label, (h, m)) in enumerate(HOME_TIMES.items()):
            cols[i % 3].button(label, key=f"home_{i}", on_click=choose_home, args=(label, h, m), width="stretch")
        st.time_input(
            "⏰ 직접 정하기",
            step=dt.timedelta(minutes=10),
            key="p_home_custom",
            on_change=choose_custom_home,
        )
        if ss.home:
            wanted = (
                f'<s>{escape(ss.home_wanted)}</s> <span class="stamp">기각</span> → ' if ss.home_wanted else ""
            )
            st.html(
                f'<div class="excuse" style="justify-content:center;font-size:1.2rem">'
                f"{wanted}<b>{escape(ss.home)}</b></div>"
                f'<p class="hand" style="font-size:1.4rem">{escape(ss.home_msg)}</p>'
            )
    nav(next_disabled=not ss.home)


# ---------------------------------------------------------------------------
# ③ 코스 짜기
# ---------------------------------------------------------------------------
def add_course(kind: str) -> None:
    if len(ss.course) < MAX_COURSE:
        ss.course = ss.course + [kind]


def pop_course() -> None:
    ss.course = ss.course[:-1]


def clear_course() -> None:
    ss.course = []


def course_chain() -> str:
    if not ss.course:
        return '<div class="chain" style="color:#8a7563">아래 버튼을 누르는 순서대로 1차, 2차, 3차…</div>'
    parts = [
        f'<span class="tag">{i + 1}차 {COURSE_TYPES[k]} {k}</span>' for i, k in enumerate(ss.course)
    ]
    return '<div class="chain">' + ' <span class="arrow">→</span> '.join(parts) + "</div>"


def page_course() -> None:
    header()
    st.markdown("## 🗺️ 오늘의 코스")
    with st.container(border=True, key="card_3"):
        st.html(course_chain())
        cols = st.columns(len(COURSE_TYPES))
        for col, (kind, emoji) in zip(cols, COURSE_TYPES.items()):
            col.button(
                f"＋ {emoji} {kind}",
                key=f"add_{kind}",
                on_click=add_course,
                args=(kind,),
                disabled=len(ss.course) >= MAX_COURSE,
                width="stretch",
            )
        left, right = st.columns(2)
        left.button("↩️ 하나 빼기", on_click=pop_course, disabled=not ss.course, width="stretch")
        right.button("🗑️ 다시 짜기", on_click=clear_course, disabled=not ss.course, width="stretch")
        st.caption("같은 것도 여러 번 넣을 수 있어. 2차 술 → 3차 술 → 4차 술도 가능 🍺")
    nav(next_disabled=not ss.course)


# ---------------------------------------------------------------------------
# ④ 차수별 메뉴판
# ---------------------------------------------------------------------------
def prefix(i: int) -> str:
    return f"p_{i}_{ss.course[i]}"


def sections(i: int) -> dict[str, list[str]]:
    kind = ss.course[i]
    if kind == "밥":
        return MEAL
    if kind == "술":
        return DRINK
    if kind == "놀거리":
        return PLAY
    concept = ss.get(f"{prefix(i)}_concept")
    return {**CAFE_DRINKS, **CAFE_CONCEPTS[concept]} if concept else {}


def picks(i: int) -> dict[str, list[str]]:
    """i차에서 고른 메뉴: {탭 이름: [메뉴...]} (직접 추가한 건 '✏️ 직접' 탭)"""
    p = prefix(i)
    out = {sec: ss.get(f"{p}_{sec}") or [] for sec in sections(i)}
    out["✏️ 직접"] = ss.get(f"{p}_custom_sel") or []
    return {k: v for k, v in out.items() if v}


def pick_random(i: int) -> None:
    secs = sections(i)
    if not secs:
        return
    sec = random.choice(list(secs))
    key = f"{prefix(i)}_{sec}"
    item = random.choice(secs[sec])
    if item not in ss[key]:
        ss[key] = ss[key] + [item]


def page_menu(i: int) -> None:
    header()
    kind = ss.course[i]
    p = prefix(i)
    st.markdown(f"## {i + 1}차 · {COURSE_TYPES[kind]} {kind}")

    with st.container(border=True, key="card_4"):
        if kind == "카페":
            st.pills("어떤 카페?", list(CAFE_CONCEPTS), key=f"{p}_concept")

        secs = sections(i)
        if secs:
            st.caption("먹고 싶은 거/하고 싶은 거 다 골라 (여러 개 가능)")
            for sec in secs:
                ss.setdefault(f"{p}_{sec}", [])
            for tab, (sec, items) in zip(st.tabs(list(secs)), secs.items()):
                with tab:
                    st.pills(sec, items, selection_mode="multi", key=f"{p}_{sec}", label_visibility="collapsed")

            ss.setdefault(f"{p}_custom_items", [])
            ss.setdefault(f"{p}_custom_sel", [])
            if ss[f"{p}_custom_items"]:
                st.pills("✏️ 직접 추가한 거", ss[f"{p}_custom_items"], selection_mode="multi", key=f"{p}_custom_sel")
            custom_input("✏️ 메뉴판에 없는 거", "예) 마라샹궈, 하이볼 2잔", f"new_{p}", f"{p}_custom_items", f"{p}_custom_sel", multi=True)
            st.button("🎲 아무거나 하나 골라줘", key=f"rand_{p}", on_click=pick_random, args=(i,), width="stretch")
        else:
            st.caption("카페 컨셉을 먼저 골라줘 ☕")

        chosen = [x for v in picks(i).values() for x in v]
        if chosen:
            st.html(f'<p class="hand" style="font-size:1.4rem">🧾 {escape(", ".join(chosen))}</p>')
    nav(next_disabled=not picks(i))


# ---------------------------------------------------------------------------
# ⑤ 예산 & 계산
# ---------------------------------------------------------------------------
def budget_text() -> str:
    return "10만원 이상 💸" if ss.p_budget >= 10 else f"{ss.p_budget}만원"


def page_budget() -> None:
    header()
    st.markdown("## 💰 예산 & 계산")
    with st.container(border=True, key="card_5"):
        st.slider("1인 예산 (만원)", 1, 10, key="p_budget", format="%d만원")
        st.html(f'<p class="hand">1인 {escape(budget_text())}</p>')
        st.radio("계산은?", PAY_WAYS, horizontal=True, key="p_pay")
    nav(next_label="주문서 뽑기 🧾")


# ---------------------------------------------------------------------------
# ⑥ 영수증
# ---------------------------------------------------------------------------
def meet_text() -> str:
    if ss.p_meet != CUSTOM_TIME:
        return ss.p_meet
    t = ss.p_meet_custom
    return hour_label(t.hour, t.minute)


def summary_lines() -> list[str]:
    today = dt.datetime.now(KST).date()
    home = ss.home + (f" ({ss.home_wanted}에 가려다 기각 ㅋ)" if ss.home_wanted else "")
    lines = [
        "🍻 오늘의 주문서 🍻",
        f"📅 {today.month}/{today.day}({'월화수목금토일'[today.weekday()]}) · 👥 {ss.p_people}명",
        f"⏰ {meet_text()} 만남 → 🏠 {home}",
        "",
    ]
    for i, kind in enumerate(ss.course):
        lines.append(f"{i + 1}차 {COURSE_TYPES[kind]} {kind}")
        if kind == "카페":
            lines.append(f"  · 컨셉: {ss.get(f'{prefix(i)}_concept')}")
        for sec, items in picks(i).items():
            lines.append(f"  · {sec}: {', '.join(items)}")
    lines += ["", f"💰 1인 {budget_text()} · {ss.p_pay}"]
    return lines


def receipt_html() -> str:
    today = dt.datetime.now(KST)
    rows = []
    n = 0
    for i, kind in enumerate(ss.course):
        rows.append(f'<div class="sec">{i + 1}차 {COURSE_TYPES[kind]} {escape(kind)}</div>')
        if kind == "카페":
            rows.append(f'<div class="sub">{escape(ss.get(f"{prefix(i)}_concept") or "")}</div>')
        for sec, items in picks(i).items():
            for item in items:
                price = JOKE_PRICES[n % len(JOKE_PRICES)]
                n += 1
                rows.append(
                    f'<div class="row"><span>{escape(item)}</span><span class="fill"></span>'
                    f'<span class="price">{escape(price)}</span></div>'
                )
    home = escape(ss.home) + (f' <span class="small">({escape(ss.home_wanted)} 기각)</span>' if ss.home_wanted else "")
    return f"""
<div class="receipt">
  <div class="center"><h3>🍻 오늘의 주문서</h3>
  <div class="small">{today:%Y-%m-%d %H:%M} · No.{random.randint(1000, 9999)}</div></div>
  <hr>
  <div class="row"><span>👥 인원</span><span class="fill"></span><span>{ss.p_people}명</span></div>
  <div class="row"><span>⏰ 만남</span><span class="fill"></span><span>{escape(meet_text())}</span></div>
  <div class="row"><span>🏠 귀가</span><span class="fill"></span><span>{home}</span></div>
  <hr>
  {''.join(rows)}
  <hr>
  <div class="total"><span>1인 예산</span><span>{escape(budget_text())}</span></div>
  <div class="total"><span>결제</span><span>{escape(ss.p_pay)}</span></div>
  <hr>
  <div class="center small">* 환불 불가 · 노쇼 시 다음 판 쏘기 *</div>
  <div class="barcode"></div>
</div>
"""


COPY_JS = """
export default function (component) {
  const { data, parentElement } = component;
  const btn = parentElement.querySelector('button');
  const msg = parentElement.querySelector('.msg');
  // 클립보드 API가 막힌 환경(iframe 등)을 위한 예전 방식
  const legacyCopy = () => {
    const ta = document.createElement('textarea');
    ta.value = data;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  };
  btn.onclick = async () => {
    let ok = false;
    try {
      await navigator.clipboard.writeText(data);
      ok = true;
    } catch (e) {
      ok = legacyCopy();
    }
    msg.textContent = ok
      ? '복사 완료! 카톡에 붙여넣기 해 📋'
      : '복사가 막혔어 😢 아래 "텍스트로 보기"에서 복사해줘';
  };
}
"""

COPY_CSS = """
button {
  width: 100%; padding: .7em; font-size: 1.05rem; cursor: pointer;
  background: #c0392b; color: #fff; border: 2px solid #3b2f2a; border-radius: 6px;
  box-shadow: 3px 3px 0 #3b2f2a; font-family: 'Gowun Dodum', sans-serif;
}
button:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 #3b2f2a; }
.msg { text-align: center; margin-top: .5em; color: #3b2f2a; min-height: 1.2em; }
"""

copy_button = st.components.v2.component(
    "today_play_copy",
    html='<button>📋 카톡에 복사하기</button><div class="msg"></div>',
    css=COPY_CSS,
    js=COPY_JS,
)


def page_receipt() -> None:
    header()
    if not ss.get("celebrated"):
        st.balloons()
        ss.celebrated = True
    st.markdown("# 주문 완료! 🧾")
    st.html(receipt_html())
    text = "\n".join(summary_lines())
    copy_button(data=text, key="copy")
    with st.expander("텍스트로 보기"):
        st.code(text, language=None)
    left, right = st.columns(2)
    left.button("← 수정하기", on_click=go, args=(ss.step - 1,), width="stretch")
    right.button("처음부터 다시", on_click=restart, width="stretch")


# ---------------------------------------------------------------------------
# 라우팅
# ---------------------------------------------------------------------------
PAGES = {"intro": page_intro, "info": page_info, "course": page_course, "budget": page_budget, "receipt": page_receipt}

ss.step = min(ss.step, len(steps()) - 1)
current = steps()[ss.step]
if current != "receipt":
    ss.celebrated = False
if current.startswith("menu:"):
    page_menu(int(current.split(":")[1]))
else:
    PAGES[current]()
