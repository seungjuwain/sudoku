
import random
import time
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="wide")

SYMBOLS = "123456789ABCDEFG"
DIFFICULTIES = ["하", "중", "상", "최상"]
CLUES = {"하": 26, "중": 23, "상": 20, "최상": 17}

# 16x16 풀이 시 단서가 너무 적은 입력을 거르기 위한 앱 기준
MIN_CLUES = {9: 17, 16: 40}

SEED = (
    "000000010"
    "400000000"
    "020000000"
    "000050407"
    "008000300"
    "001090000"
    "300400200"
    "050100000"
    "000806000"
)

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding: 1.2rem 0.6rem;
}
h1, h2, h3 {
    text-align: center;
}
div.stButton > button {
    width: 100%;
    min-height: 42px;
    font-size: 16px;
}
div[data-testid="stHorizontalBlock"] {
    gap: 2px !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    padding: 0 !important;
    min-width: 0 !important;
}
div[data-testid="stTextInput"] {
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stTextInput"] input {
    height: 38px !important;
    min-height: 38px !important;
    text-align: center !important;
    font-size: 19px !important;
    font-weight: 500 !important;
    padding: 0 !important;
    border-radius: 0 !important;
    border: 1px solid #999 !important;
    background: white !important;
    color: #234f91 !important;
}
div[data-testid="stTextInput"] input:focus {
    background: #e8dcff !important;
    border: 2px solid #8d62d5 !important;
    box-shadow: none !important;
}
div.st-key-selected-cell div[data-testid="stTextInput"] input {
    background: #e8dcff !important;
}
.given-cell input {
    background: #e9eef5 !important;
    color: #254f91 !important;
    font-weight: 700 !important;
}
.timer-outer {
    width: 100%;
    height: 17px;
    background: #dedede;
    border-radius: 10px;
    overflow: hidden;
    margin: 8px 0 12px 0;
}
.timer-inner {
    height: 100%;
    border-radius: 10px;
    transition: width 0.15s linear;
}
.player-label {
    text-align: center;
    font-size: 23px;
    font-weight: 700;
    margin: 5px 0;
}
.rule-card {
    padding: 16px;
    border: 1px solid #b8c8dc;
    border-radius: 10px;
    background: #f0f6ff;
    color: #24364c;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 스도쿠 풀이 엔진
# =========================================================

def candidates(board, r, c, n, box):
    used = set(board[r])
    used.update(board[i][c] for i in range(n))

    br = (r // box) * box
    bc = (c // box) * box

    for i in range(br, br + box):
        for j in range(bc, bc + box):
            used.add(board[i][j])

    return set(range(1, n + 1)) - used


def find_empty(board, n, box):
    best = None
    best_options = None

    for r in range(n):
        for c in range(n):
            if board[r][c] != 0:
                continue

            options = candidates(board, r, c, n, box)

            if not options:
                return r, c, set()

            if best is None or len(options) < len(best_options):
                best = (r, c)
                best_options = options

                if len(options) == 1:
                    return r, c, options

    if best is None:
        return None, None, None

    return best[0], best[1], best_options


def solve_count(board, n, box, limit=2, max_nodes=300000,
                max_seconds=4.0):
    """
    limit=2:
      0개: 해답 없음
      1개: 유일해인지 확인 가능
      2개: 복수 해답

    탐색 한도에 도달하면 유일해라고 잘못 판정하지 않습니다.
    """
    count = 0
    first_solution = None
    nodes = 0
    start = time.monotonic()
    exhausted = True

    def backtrack():
        nonlocal count, first_solution, nodes, exhausted

        if count >= limit:
            return

        nodes += 1

        if nodes > max_nodes or time.monotonic() - start > max_seconds:
            exhausted = False
            return

        r, c, options = find_empty(board, n, box)

        if r is None:
            count += 1
            if first_solution is None:
                first_solution = [row[:] for row in board]
            return

        if not options:
            return

        for value in options:
            board[r][c] = value
            backtrack()
            board[r][c] = 0

            if count >= limit or not exhausted:
                return

    backtrack()

    return count, first_solution, exhausted


def validate(board, n, box):
    for r in range(n):
        values = [v for v in board[r] if v]
        if len(values) != len(set(values)):
            return False, f"{r + 1}행에 중복 숫자가 있습니다."

    for c in range(n):
        values = [board[r][c] for r in range(n) if board[r][c]]
        if len(values) != len(set(values)):
            return False, f"{c + 1}열에 중복 숫자가 있습니다."

    for br in range(0, n, box):
        for bc in range(0, n, box):
            values = [
                board[r][c]
                for r in range(br, br + box)
                for c in range(bc, bc + box)
                if board[r][c]
            ]

            if len(values) != len(set(values)):
                return False, "같은 구역에 중복 숫자가 있습니다."

    return True, ""


# =========================================================
# 퍼즐 생성
# =========================================================

def generate_puzzle(target_clues):
    seed = [
        [int(x) for x in SEED[r * 9:(r + 1) * 9]]
        for r in range(9)
    ]

    count, seed_solution, complete = solve_count(
        [row[:] for row in seed],
        9, 3, limit=2
    )

    if count != 1 or not complete:
        raise RuntimeError("기본 퍼즐의 유일해 검증에 실패했습니다.")

    def shuffled_groups():
        groups = [
            list(range(3 * i, 3 * i + 3))
            for i in range(3)
        ]
        random.shuffle(groups)
        return [v for group in groups for v in random.sample(group, 3)]

    rows = shuffled_groups()
    cols = shuffled_groups()

    digits = list(range(1, 10))
    random.shuffle(digits)
    mapping = {i + 1: digits[i] for i in range(9)}

    transpose = random.choice([True, False])

    def transform(board):
        result = [[board[r][c] for c in cols] for r in rows]

        if transpose:
            result = [list(row) for row in zip(*result)]

        return [
            [mapping[v] if v else 0 for v in row]
            for row in result
        ]

    puzzle = transform(seed)
    solution = transform(seed_solution)

    empty = [
        (r, c)
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] == 0
    ]

    random.shuffle(empty)

    for r, c in empty[:target_clues - 17]:
        puzzle[r][c] = solution[r][c]

    assert sum(v != 0 for row in puzzle for v in row) == target_clues

    return puzzle, solution


# =========================================================
# 상태 및 셀 입력 관리
# =========================================================

def clear_cell_keys(n):
    for r in range(n):
        for c in range(n):
            key = f"cell_{r}_{c}"
            if key in st.session_state:
                del st.session_state[key]


def prepare_board(board, mode):
    n = len(board)
    clear_cell_keys(n)

    st.session_state.board = [row[:] for row in board]
    st.session_state.selected = None
    st.session_state.board_mode = mode


def cell_changed(r, c, mode):
    key = f"cell_{r}_{c}"
    raw = str(st.session_state.get(key, "")).strip().upper()

    st.session_state.selected = (r, c)

    n = len(st.session_state.board)
    allowed = SYMBOLS[:n]

    if raw == "":
        if mode == "solve":
            st.session_state.board[r][c] = 0
        return

    if len(raw) != 1 or raw not in allowed:
        st.session_state[key] = ""
        return

    value = SYMBOLS.index(raw) + 1

    if mode == "solve":
        st.session_state.board[r][c] = value
        st.session_state.solve_result = None
        return

    if mode == "puzzle":
        if (r, c) in st.session_state.locked:
            st.session_state[key] = ""
            return

        if st.session_state.board[r][c] != 0:
            st.session_state[key] = SYMBOLS[
                st.session_state.board[r][c] - 1
            ]
            return

        if value == st.session_state.solution[r][c]:
            st.session_state.board[r][c] = value
            return

        st.session_state.board[r][c] = 0
        st.session_state[key] = ""

        st.session_state.lives -= 1

        if st.session_state.lives <= 0:
            st.session_state.lives = 0
            st.session_state.game_over = True

        return

    if mode == "versus":
        if st.session_state.phase != "active":
            st.session_state[key] = ""
            return

        if time.time() >= st.session_state.deadline:
            st.session_state.winner = (
                2 if st.session_state.player == 1 else 1
            )
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "시간 초과"
            st.session_state[key] = ""
            return

        if (r, c) in st.session_state.locked:
            st.session_state[key] = ""
            return

        if st.session_state.board[r][c] != 0:
            st.session_state[key] = SYMBOLS[
                st.session_state.board[r][c] - 1
            ]
            return

        if value != st.session_state.solution[r][c]:
            st.session_state.winner = (
                2 if st.session_state.player == 1 else 1
            )
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "오답"
            st.session_state[key] = ""
            return

        # 정답 입력
        st.session_state.board[r][c] = value

        # 모든 칸을 맞혔는지 확인
        if all(
            v != 0
            for row in st.session_state.board
            for v in row
        ):
            next_level = st.session_state.level_index + 1

            if next_level >= len(DIFFICULTIES):
                st.session_state.phase = "champion"
                st.session_state.winner = st.session_state.player
                return

            # 다음 난이도. 성공한 플레이어가 계속 시작합니다.
            st.session_state.level_index = next_level
            st.session_state.player = st.session_state.player
            make_versus_level()
            return

        # 성공했으면 상대에게 턴 이동
        st.session_state.player = (
            2 if st.session_state.player == 1 else 1
        )
        st.session_state.turn_start = time.time()
        st.session_state.deadline = time.time() + 20


# =========================================================
# 게임 초기화
# =========================================================

def make_versus_level():
    difficulty = DIFFICULTIES[st.session_state.level_index]
    puzzle, solution = generate_puzzle(CLUES[difficulty])

    prepare_board(puzzle, "versus")

    st.session_state.solution = solution
    st.session_state.locked = {
        (r, c)
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] != 0
    }

    st.session_state.turn_start = time.time()
    st.session_state.deadline = time.time() + 20
    st.session_state.phase = "active"


# =========================================================
# 스도쿠 판 표시
# =========================================================

def draw_board(n, mode):
    box = 3 if n == 9 else 4
    selected = st.session_state.get("selected")
    locked = st.session_state.get("locked", set())

    for r in range(n):
        cols = st.columns(n, gap="small")

        for c in range(n):
            key = f"cell_{r}_{c}"
            value = st.session_state.board[r][c]

            if key not in st.session_state:
                st.session_state[key] = (
                    SYMBOLS[value - 1] if value else ""
                )

            is_selected = selected == (r, c)
            is_given = (r, c) in locked

            background = (
                "#e8dcff" if is_selected
                else "#dceeff" if selected and (
                    selected[0] == r or selected[1] == c
                )
                else "#e9eef5" if is_given
                else "#ffffff"
            )

            color = "#254f91" if is_given else "#222222"

            border_left = (
                "2px solid #222"
                if c % box == 0
                else "1px solid #aaa"
            )

            border_top = (
                "2px solid #222"
                if r % box == 0
                else "1px solid #aaa"
            )

            border_right = (
                "2px solid #222"
                if (c + 1) % box == 0
                else "1px solid #aaa"
            )

            border_bottom = (
                "2px solid #222"
                if (r + 1) % box == 0
                else "1px solid #aaa"
            )

            with cols[c]:
                st.markdown(
                    f"""
                    <style>
                    div.st-key-{key} input {{
                        background: {background} !important;
                        color: {color} !important;
                        border-left: {border_left} !important;
                        border-top: {border_top} !important;
                        border-right: {border_right} !important;
                        border-bottom: {border_bottom} !important;
                        font-weight: {'700' if is_given else '500'} !important;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                st.text_input(
                    f"{r+1}-{c+1}",
                    key=key,
                    max_chars=1,
                    label_visibility="collapsed",
                    disabled=is_given,
                    on_change=cell_changed,
                    args=(r, c, mode),
                )


# =========================================================
# 남은 숫자 표시
# =========================================================

def show_remaining(n):
    st.markdown("#### 숫자별 남은 개수")

    counts = {
        v: sum(
            cell == v
            for row in st.session_state.board
            for cell in row
        )
        for v in range(1, n + 1)
    }

    cols = st.columns(n, gap="small")

    for i, col in enumerate(cols, start=1):
        remaining = n - counts[i]

        with col:
            st.markdown(
                f"""
                <div style="
                    border:1px solid #b5c7df;
                    border-radius:5px;
                    text-align:center;
                    padding:5px 1px;
                    background:#edf5ff;
                    color:#28548e;
                    line-height:1.2;
                ">
                    <div style="
                        font-size:22px;
                        font-weight:700;
                    ">{SYMBOLS[i-1]}</div>
                    <div style="
                        font-size:12px;
                        margin-top:4px;
                        color:#52657d;
                    ">{remaining}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# 타이머
# =========================================================

def show_timer():
    remaining = max(
        0,
        st.session_state.deadline - time.time()
    )

    percent = remaining / 20 * 100

    color = "#e44b4b" if remaining <= 5 else "#4285d4"

    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            font-weight:700;
            margin-bottom:4px;
        ">
            <span>남은 시간</span>
            <span>{remaining:.1f}초</span>
        </div>

        <div class="timer-outer">
            <div class="timer-inner"
                 style="width:{percent}%;background:{color};">
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return remaining


# =========================================================
# 초기 상태
# =========================================================

defaults = {
    "page": "home",
    "solve_result": None,
    "lives": 3,
    "game_over": False,
    "phase": "rules",
    "level_index": 0,
    "player": 1,
    "winner": None,
    "finish_reason": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 홈
# =========================================================

if st.session_state.page == "home":
    st.title("스도쿠")

    a, b = st.columns(2)

    with a:
        if st.button("풀이", type="primary"):
            st.session_state.page = "solve_select"
            st.rerun()

    with b:
        if st.button("문제", type="primary"):
            st.session_state.page = "puzzle_select"
            st.rerun()


# =========================================================
# 풀이 규격 선택
# =========================================================

elif st.session_state.page == "solve_select":
    st.title("스도쿠 풀이")

    n = st.radio(
        "규격",
        [9, 16],
        format_func=lambda x: f"{x} × {x}",
        horizontal=True,
    )

    if st.button("빈 판 만들기", type="primary"):
        prepare_board(
            [[0] * n for _ in range(n)],
            "solve"
        )
        st.session_state.solve_n = n
        st.session_state.solve_result = None
        st.session_state.page = "solve_board"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# 풀이 화면
# =========================================================

elif st.session_state.page == "solve_board":
    n = st.session_state.solve_n

    st.title(f"{n} × {n} 스도쿠")
    st.caption(
        "셀을 선택하고 숫자를 입력하십시오. "
        "한 글자 입력 즉시 반영됩니다."
    )

    draw_board(n, "solve")
    show_remaining(n)

    if st.button("완료", type="primary"):
        board = [row[:] for row in st.session_state.board]
        box = 3 if n == 9 else 4

        clue_count = sum(v != 0 for row in board for v in row)

        valid, reason = validate(board, n, box)

        if not valid:
            st.session_state.solve_result = (
                "불가능",
                f"규칙 위반: {reason}"
            )

        elif clue_count < MIN_CLUES[n]:
            st.session_state.solve_result = (
                "불가능",
                f"단서 부족: 현재 {clue_count}개입니다. "
                f"최소 {MIN_CLUES[n]}개 이상의 단서가 필요합니다."
            )

        else:
            count, solution, complete = solve_count(
                [row[:] for row in board],
                n,
                box,
                limit=2,
                max_seconds=6.0,
            )

            if count == 0 and complete:
                st.session_state.solve_result = (
                    "불가능",
                    "규칙 위반: 입력한 단서로는 해답을 만들 수 없습니다."
                )

            elif count >= 2:
                st.session_state.solve_result = (
                    "불가능",
                    "단서 부족: 가능한 해답이 여러 개입니다. "
                    "단서를 더 입력해 주십시오."
                )

            elif not complete:
                st.session_state.solve_result = (
                    "불가능",
                    "풀이 검증 시간 초과: 단서를 더 입력한 후 다시 시도해 주십시오."
                )

            elif count == 1:
                st.session_state.solve_result = (
                    "가능",
                    solution
                )

            else:
                st.session_state.solve_result = (
                    "불가능",
                    "해답을 확인할 수 없습니다."
                )

        st.rerun()

    result = st.session_state.solve_result

    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.warning(result[1])

        else:
            st.success("유일한 해답을 찾았습니다.")

            st.markdown("### 완성된 스도쿠")

            solution = result[1]

            for row in solution:
                st.write("　".join(
                    SYMBOLS[v - 1] for v in row
                ))

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# 문제 난이도 선택
# =========================================================

elif st.session_state.page == "puzzle_select":
    st.title("스도쿠 문제")

    difficulty = st.radio(
        "난이도 선택",
        DIFFICULTIES,
        horizontal=True,
    )

    st.write(f"초기 단서: {CLUES[difficulty]}개")

    if st.button("문제 생성", type="primary"):
        puzzle, solution = generate_puzzle(CLUES[difficulty])

        prepare_board(puzzle, "puzzle")

        st.session_state.solution = solution

        st.session_state.locked = {
            (r, c)
            for r in range(9)
            for c in range(9)
            if puzzle[r][c] != 0
        }

        st.session_state.lives = 3
        st.session_state.game_over = False
        st.session_state.page = "puzzle_play"

        st.rerun()

    st.divider()

    st.markdown("### 1 vs 1 대전")

    st.write(
        "두 명이 번갈아 가며 한 칸씩 정답을 입력하는 대전 모드입니다."
    )

    if st.button("1 vs 1 시작", type="primary"):
        st.session_state.level_index = 0
        st.session_state.player = 1
        st.session_state.winner = None
        st.session_state.finish_reason = ""
        st.session_state.phase = "rules"
        st.session_state.page = "versus"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# 일반 문제 풀이
# =========================================================

elif st.session_state.page == "puzzle_play":
    st.title("스도쿠 문제")

    st.markdown(
        f"<div style='text-align:center;font-size:28px'>"
        f"{'❤️ ' * st.session_state.lives}</div>",
        unsafe_allow_html=True,
    )

    if st.session_state.game_over:
        st.error("실패했습니다. 목숨을 모두 사용했습니다.")

    else:
        draw_board(9, "puzzle")
        show_remaining(9)

        if all(
            v != 0
            for row in st.session_state.board
            for v in row
        ):
            if st.session_state.board == st.session_state.solution:
                st.success("정답입니다!")

    a, b = st.columns(2)

    with a:
        if st.button("새 문제"):
            st.session_state.page = "puzzle_select"
            st.rerun()

    with b:
        if st.button("처음으로"):
            st.session_state.page = "home"
            st.rerun()


# =========================================================
# 1vs1 룰 설명
# =========================================================

elif st.session_state.page == "versus":
    st.title("1 vs 1 스도쿠 대전")

    if st.session_state.phase == "rules":
        st.markdown("""
        <div class="rule-card">
        <h3>대전 규칙</h3>

        1. Player 1부터 시작합니다.<br>
        2. 각 플레이어에게는 한 턴당 20초가 주어집니다.<br>
        3. 제한 시간 안에 빈칸 한 개를 정확히 채우면
        상대 플레이어에게 턴이 넘어갑니다.<br>
        4. 틀린 숫자를 입력하거나 20초 안에 입력하지 못하면
        해당 플레이어가 패배합니다.<br>
        5. 모든 칸을 정확하게 채우면 다음 난이도로 넘어갑니다.<br>
        6. 난이도는 하 → 중 → 상 → 최상 순서입니다.<br>
        7. 다음 난이도에서도 마지막으로 성공한 플레이어가
        먼저 시작합니다.
        </div>
        """, unsafe_allow_html=True)

        st.write("첫 번째 판은 하 난이도입니다.")

        if st.button("대전 시작", type="primary"):
            st.session_state.level_index = 0
            st.session_state.player = 1
            st.session_state.phase = "ready"
            st.session_state.ready_until = time.time() + 3
            st.rerun()

    elif st.session_state.phase == "ready":
        st_autorefresh(interval=200, key="versus_ready")

        remaining = max(
            0,
            st.session_state.ready_until - time.time()
        )

        st.markdown(
            f"<h2>{remaining:.0f}</h2>",
            unsafe_allow_html=True,
        )

        st.info("잠시 후 Player 1부터 시작합니다.")

        if remaining <= 0:
            make_versus_level()
            st.rerun()

    elif st.session_state.phase == "active":
        st_autorefresh(interval=200, key="versus_timer")

        remaining = show_timer()

        if remaining <= 0:
            st.session_state.winner = (
                2 if st.session_state.player == 1 else 1
            )
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "시간 초과"
            st.rerun()

        st.markdown(
            f"<div class='player-label'>"
            f"Player {st.session_state.player} 차례"
            f"</div>",
            unsafe_allow_html=True,
        )

        difficulty = DIFFICULTIES[
            st.session_state.level_index
        ]

        st.caption(
            f"현재 난이도: {difficulty} "
            f"({st.session_state.level_index + 1}/4)"
        )

        # 타이머 바는 스도쿠 판 바로 위에 배치됩니다.
        draw_board(9, "versus")
        show_remaining(9)

        st.caption(
            "한 칸을 정확하게 입력하면 상대에게 턴이 넘어갑니다."
        )

    elif st.session_state.phase == "finished":
        st.title("대전 종료")

        winner = st.session_state.winner

        st.error(
            f"Player {winner} 승리!"
        )

        st.write(
            f"종료 사유: Player "
            f"{3 - winner}의 {st.session_state.finish_reason}"
        )

        if st.button("다시 대전하기", type="primary"):
            st.session_state.phase = "rules"
            st.session_state.page = "versus"
            st.session_state.winner = None
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()

    elif st.session_state.phase == "champion":
        st.title("최종 우승")

        st.balloons()

        st.success(
            f"Player {st.session_state.winner} "
            "최종 우승!"
        )

        st.write("하, 중, 상, 최상 모든 난이도를 완료했습니다.")

        if st.button("다시 대전하기", type="primary"):
            st.session_state.phase = "rules"
            st.session_state.page = "versus"
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()
