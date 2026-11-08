
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import random
import time
import math

# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="Classic Sudoku",
    page_icon="🔢",
    layout="wide"
)

SYMBOLS = "123456789ABCDEFG"

DIFFICULTIES = ["하", "중", "상", "최상"]

CLUES = {
    "하": 26,
    "중": 23,
    "상": 20,
    "최상": 17
}

MIN_CLUES = {
    9: 17,
    16: 40
}

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

# =========================================================
# 디자인
# =========================================================

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding: 1rem 0.6rem;
}

/* 셀 버튼 공통 */
div[class*="st-key-cell_"] button {
    width: 100%;
    min-width: 0 !important;
    height: auto;
    aspect-ratio: 1 / 1;
    padding: 0 !important;
    border-radius: 0 !important;
    font-size: clamp(12px, 2vw, 22px) !important;
    font-weight: 500;
    line-height: 1;
    box-shadow: none !important;
}

/* 셀 버튼 내부 */
div[class*="st-key-cell_"] button p {
    margin: 0 !important;
    padding: 0 !important;
}

/* 선택 셀 */
div[class*="st-key-cell_"] button.selected-cell {
    background: #e8dcff !important;
    color: #333 !important;
}

/* 하늘색 행과 열 */
div[class*="st-key-cell_"] button.related-cell {
    background: #dceeff !important;
    color: #333 !important;
}

/* 기본 셀 */
div[class*="st-key-cell_"] button.normal-cell {
    background: #ffffff !important;
    color: #222 !important;
}

/* 초기 단서 */
div[class*="st-key-cell_"] button.given-cell {
    color: #28548e !important;
    font-weight: 800 !important;
}

/* 남은 숫자 */
.remaining-number {
    text-align: center;
    background: #edf5ff;
    border: 1px solid #b5c7df;
    border-radius: 5px;
    padding: 5px 1px;
    min-height: 58px;
}

.remaining-number .digit {
    font-size: 22px;
    font-weight: 800;
    color: #28548e;
}

.remaining-number .count {
    font-size: 12px;
    color: #52657d;
    margin-top: 3px;
}

/* 하트 */
.hearts {
    text-align: center;
    font-size: 30px;
    margin: 10px;
}

/* 대전 타이머 */
.timer-background {
    width: 100%;
    height: 18px;
    background: #dedede;
    border-radius: 10px;
    overflow: hidden;
    margin: 8px 0 14px;
}

.timer-progress {
    height: 100%;
    border-radius: 10px;
}

/* 대전 규칙 */
.rule-card {
    background: #f0f6ff;
    color: #24364c;
    padding: 18px;
    border-radius: 10px;
    line-height: 1.9;
    border: 1px solid #b8c8dc;
}

/* 플레이어 */
.player-label {
    text-align: center;
    font-size: 25px;
    font-weight: 800;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 스도쿠 엔진
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


def solve_count(
    board,
    n,
    box,
    limit=2,
    max_nodes=300000,
    max_seconds=6
):

    count = 0
    solution = None
    nodes = 0
    exhausted = True
    start = time.monotonic()

    def backtrack():

        nonlocal count, solution, nodes, exhausted

        if count >= limit:
            return

        nodes += 1

        if (
            nodes > max_nodes
            or time.monotonic() - start > max_seconds
        ):
            exhausted = False
            return

        r, c, options = find_empty(board, n, box)

        if r is None:

            count += 1

            if solution is None:
                solution = [row[:] for row in board]

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

    return count, solution, exhausted


def validate(board, n, box):

    for r in range(n):

        values = [v for v in board[r] if v]

        if len(values) != len(set(values)):
            return False, f"{r+1}행에 중복 숫자가 있습니다."

    for c in range(n):

        values = [
            board[r][c]
            for r in range(n)
            if board[r][c]
        ]

        if len(values) != len(set(values)):
            return False, f"{c+1}열에 중복 숫자가 있습니다."

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
# 문제 생성
# =========================================================

def generate_puzzle(target_clues):

    seed = [
        [
            int(SEED[r * 9 + c])
            for c in range(9)
        ]
        for r in range(9)
    ]

    count, seed_solution, complete = solve_count(
        [row[:] for row in seed],
        9,
        3,
        limit=2
    )

    if count != 1 or not complete:
        raise RuntimeError("기본 퍼즐 검증에 실패했습니다.")

    def shuffled_groups():

        groups = [
            list(range(3 * i, 3 * i + 3))
            for i in range(3)
        ]

        random.shuffle(groups)

        return [
            value
            for group in groups
            for value in random.sample(group, 3)
        ]

    rows = shuffled_groups()
    cols = shuffled_groups()

    digits = list(range(1, 10))
    random.shuffle(digits)

    mapping = {
        i + 1: digits[i]
        for i in range(9)
    }

    transpose = random.choice([True, False])

    def transform(board):

        result = [
            [board[r][c] for c in cols]
            for r in rows
        ]

        if transpose:
            result = [list(row) for row in zip(*result)]

        return [
            [
                mapping[v] if v else 0
                for v in row
            ]
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
# 상태 관리
# =========================================================

def initialize_board(board, mode):

    st.session_state.board = [
        row[:] for row in board
    ]

    st.session_state.selected = None
    st.session_state.board_mode = mode

    st.session_state.entry_value = ""

    n = len(board)

    st.session_state.locked = {
        (r, c)
        for r in range(n)
        for c in range(n)
        if board[r][c] != 0
    }

    st.session_state.locked_values = {
        (r, c): board[r][c]
        for r in range(n)
        for c in range(n)
        if board[r][c] != 0
    }


def select_cell(r, c):

    st.session_state.selected = (r, c)
    st.session_state.entry_value = ""


# =========================================================
# 셀 선택 및 입력
# =========================================================

def draw_board(n, mode):

    box = 3 if n == 9 else 4

    selected = st.session_state.selected
    locked = st.session_state.locked

    # 정사각형 셀 버튼으로 판 구성
    for r in range(n):

        cols = st.columns(n, gap="small")

        for c in range(n):

            key = f"cell_{r}_{c}"
            value = st.session_state.board[r][c]

            is_selected = selected == (r, c)
            is_given = (r, c) in locked

            in_related_area = (
                selected is not None
                and (
                    selected[0] == r
                    or selected[1] == c
                    or (
                        selected[0] // box == r // box
                        and selected[1] // box == c // box
                    )
                )
            )

            if is_selected:
                cell_class = "selected-cell"

            elif in_related_area:
                cell_class = "related-cell"

            else:
                cell_class = "normal-cell"

            if is_given:
                cell_class += " given-cell"

            label = SYMBOLS[value - 1] if value else " "

            # 셀별 색상 지정
            st.markdown(
                f"""
                <style>
                .st-key-{key} button {{
                    background-color: {
                        '#e8dcff' if is_selected
                        else '#dceeff' if in_related_area
                        else '#e9eef5' if is_given
                        else '#ffffff'
                    } !important;

                    color: {
                        '#28548e' if is_given else '#222222'
                    } !important;

                    border: 1px solid #777777 !important;
                    border-radius: 0 !important;
                    padding: 0 !important;
                    font-weight: {
                        '800' if is_given else '500'
                    } !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

            with cols[c]:

                st.button(
                    label,
                    key=key,
                    use_container_width=True,
                    on_click=select_cell,
                    args=(r, c)
                )


# =========================================================
# 선택한 셀에 숫자 입력
# =========================================================

def apply_entry():

    selected = st.session_state.selected

    if selected is None:
        return

    r, c = selected

    key = "entry_value"

    raw = st.session_state.get(key, "")

    if not raw:
        return

    n = len(st.session_state.board)

    if raw not in SYMBOLS[:n]:
        st.session_state.entry_value = ""
        return

    value = SYMBOLS.index(raw) + 1

    # 초기 단서 보호
    if (r, c) in st.session_state.locked:
        st.session_state.entry_value = ""
        return

    mode = st.session_state.board_mode

    if mode == "solve":

        st.session_state.board[r][c] = value
        st.session_state.solve_result = None
        st.session_state.entry_value = ""
        return

    if mode == "puzzle":

        if st.session_state.board[r][c] != 0:
            st.session_state.entry_value = ""
            return

        if value == st.session_state.solution[r][c]:

            st.session_state.board[r][c] = value

        else:

            st.session_state.lives -= 1

            if st.session_state.lives <= 0:
                st.session_state.lives = 0
                st.session_state.game_over = True

        st.session_state.entry_value = ""
        return

    if mode == "versus":

        if st.session_state.phase != "active":
            st.session_state.entry_value = ""
            return

        if time.time() >= st.session_state.deadline:

            st.session_state.winner = 3 - st.session_state.player
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "시간 초과"
            st.session_state.entry_value = ""
            return

        if st.session_state.board[r][c] != 0:
            st.session_state.entry_value = ""
            return

        if value != st.session_state.solution[r][c]:

            st.session_state.winner = 3 - st.session_state.player
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "오답"
            st.session_state.entry_value = ""
            return

        st.session_state.board[r][c] = value

        # 모든 칸 완료
        if all(
            v != 0
            for row in st.session_state.board
            for v in row
        ):

            if st.session_state.level_index == 3:

                st.session_state.winner = st.session_state.player
                st.session_state.phase = "champion"
                st.session_state.entry_value = ""
                return

            st.session_state.level_index += 1

            # 마지막 정답자부터 다음 난이도 시작
            make_versus_level()

            return

        # 상대에게 턴 전달
        st.session_state.player = 3 - st.session_state.player

        st.session_state.turn_start = time.time()
        st.session_state.deadline = time.time() + 20

        st.session_state.entry_value = ""


def show_entry(n, mode):

    selected = st.session_state.selected

    if selected is None:
        st.info("스도쿠 판에서 입력할 셀을 선택하십시오.")
        return

    r, c = selected

    if (r, c) in st.session_state.locked:

        st.info("초기 단서는 변경할 수 없습니다.")
        return

    if st.session_state.board[r][c] != 0:

        st.info("이미 숫자가 입력된 셀입니다.")
        return

    st.markdown(
        f"**선택한 셀: {r+1}행 {c+1}열**"
    )

    st.selectbox(
        "입력할 숫자",
        options=[""] + list(SYMBOLS[:n]),
        key="entry_value",
        on_change=apply_entry,
        label_visibility="collapsed",
        format_func=lambda x: x if x else "숫자를 선택하십시오."
    )


# =========================================================
# 남은 개수 표시
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

            # HTML을 한 줄로 출력하여 코드 블록으로
            # 오인되는 문제 방지
            st.markdown(
                f'<div class="remaining-number">'
                f'<div class="digit">{SYMBOLS[i-1]}</div>'
                f'<div class="count">{remaining}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# =========================================================
# 1vs1 퍼즐 생성
# =========================================================

def make_versus_level():

    difficulty = DIFFICULTIES[
        st.session_state.level_index
    ]

    puzzle, solution = generate_puzzle(
        CLUES[difficulty]
    )

    initialize_board(puzzle, "versus")

    st.session_state.solution = solution

    st.session_state.deadline = time.time() + 20
    st.session_state.turn_start = time.time()

    st.session_state.phase = "active"


# =========================================================
# 타이머
# =========================================================

def show_timer():

    remaining = max(
        0,
        st.session_state.deadline - time.time()
    )

    percentage = remaining / 20 * 100

    color = "#e44b4b" if remaining <= 5 else "#4285d4"

    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;">
            <b>남은 시간</b>
            <b>{remaining:.1f}초</b>
        </div>
        <div class="timer-background">
            <div class="timer-progress"
                 style="width:{percentage}%;background:{color};">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    return remaining


# =========================================================
# 초기 세션 상태
# =========================================================

defaults = {
    "page": "home",
    "selected": None,
    "solve_result": None,
    "lives": 3,
    "game_over": False,
    "phase": "rules",
    "level_index": 0,
    "player": 1,
    "winner": None,
    "finish_reason": "",
    "entry_value": ""
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 메인 화면
# =========================================================

if st.session_state.page == "home":

    st.title("Classic Sudoku")

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
        "규격 선택",
        [9, 16],
        horizontal=True,
        format_func=lambda x: f"{x} × {x}"
    )

    if st.button("빈 판 만들기", type="primary"):

        initialize_board(
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

    draw_board(n, "solve")

    show_entry(n, "solve")

    show_remaining(n)

    if st.button("완료", type="primary"):

        board = [
            row[:] for row in st.session_state.board
        ]

        box = 3 if n == 9 else 4

        clue_count = sum(
            v != 0
            for row in board
            for v in row
        )

        valid, reason = validate(
            board, n, box
        )

        if not valid:

            st.session_state.solve_result = (
                "불가능",
                f"규칙 위반: {reason}"
            )

        elif clue_count < MIN_CLUES[n]:

            st.session_state.solve_result = (
                "불가능",
                f"단서 부족: 현재 {clue_count}개입니다. "
                f"최소 {MIN_CLUES[n]}개가 필요합니다."
            )

        else:

            count, solution, complete = solve_count(
                [row[:] for row in board],
                n,
                box,
                limit=2
            )

            if not complete:

                result = (
                    "불가능",
                    "풀이 검증 시간 초과: 단서를 더 입력해 주십시오."
                )

            elif count == 0:

                result = (
                    "불가능",
                    "규칙 위반: 입력한 단서로 해답을 만들 수 없습니다."
                )

            elif count >= 2:

                result = (
                    "불가능",
                    "단서 부족: 가능한 해답이 여러 개입니다."
                )

            else:

                result = (
                    "가능",
                    solution
                )

            st.session_state.solve_result = result

        st.rerun()

    result = st.session_state.solve_result

    if result:

        if result[0] == "불가능":

            st.error("풀이 불가능")
            st.warning(result[1])

        else:

            st.success("풀이 완료")

            solution = result[1]

            st.markdown("### 완성된 스도쿠")

            for row in solution:

                st.write(
                    "　".join(
                        SYMBOLS[v-1]
                        for v in row
                    )
                )

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
        horizontal=True
    )

    st.write(
        f"초기 단서: {CLUES[difficulty]}개"
    )

    if st.button("문제 생성", type="primary"):

        puzzle, solution = generate_puzzle(
            CLUES[difficulty]
        )

        initialize_board(puzzle, "puzzle")

        st.session_state.solution = solution
        st.session_state.lives = 3
        st.session_state.game_over = False

        st.session_state.page = "puzzle_play"

        st.rerun()

    st.divider()

    st.subheader("1 vs 1 스도쿠 대전")

    if st.button("1 vs 1 시작", type="primary"):

        st.session_state.level_index = 0
        st.session_state.player = 1
        st.session_state.winner = None
        st.session_state.phase = "rules"

        st.session_state.page = "versus"

        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# 일반 문제 플레이
# =========================================================

elif st.session_state.page == "puzzle_play":

    st.title("스도쿠 문제")

    st.markdown(
        f'<div class="hearts">'
        f'{"❤️ " * st.session_state.lives}'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.session_state.game_over:

        st.error("실패했습니다. 목숨을 모두 사용했습니다.")

    else:

        draw_board(9, "puzzle")

        show_entry(9, "puzzle")

        show_remaining(9)

        if all(
            v != 0
            for row in st.session_state.board
            for v in row
        ):

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
# 1vs1 대전
# =========================================================

elif st.session_state.page == "versus":

    st.title("1 vs 1 스도쿠 대전")

    # -----------------------------------------------------
    # 룰 설명
    # -----------------------------------------------------

    if st.session_state.phase == "rules":

        st.markdown("""
        <div class="rule-card">
        <h3>대전 규칙</h3>
        1. Player 1부터 시작합니다.<br>
        2. 각 턴에는 20초가 주어집니다.<br>
        3. 제한 시간 안에 한 칸을 정확하게 채우면 상대 차례가 됩니다.<br>
        4. 오답을 입력하거나 제한 시간이 끝나면 패배합니다.<br>
        5. 모든 칸을 채우면 다음 난이도로 올라갑니다.<br>
        6. 난이도는 하 → 중 → 상 → 최상 순서입니다.<br>
        7. 난이도가 올라가도 마지막으로 성공한 플레이어가 먼저 시작합니다.
        </div>
        """, unsafe_allow_html=True)

        if st.button("대전 시작", type="primary"):

            st.session_state.level_index = 0
            st.session_state.player = 1

            st.session_state.phase = "ready"
            st.session_state.ready_until = time.time() + 3

            st.rerun()

    # -----------------------------------------------------
    # 카운트다운
    # -----------------------------------------------------

    elif st.session_state.phase == "ready":

        st_autorefresh(
            interval=100,
            key="ready_timer"
        )

        remaining = (
            st.session_state.ready_until - time.time()
        )

        if remaining <= 0:

            make_versus_level()

            st.rerun()

        else:

            countdown = math.ceil(remaining)

            st.markdown(
                f"""
                <div style="text-align:center;padding:35px 0;">
                    <h2>대전 준비</h2>
                    <div style="font-size:72px;font-weight:800;">
                        {countdown}
                    </div>
                    <p>Player 1부터 시작합니다.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # 대전 진행
    # -----------------------------------------------------

    elif st.session_state.phase == "active":

        st_autorefresh(
            interval=100,
            key="active_timer"
        )

        remaining = (
            st.session_state.deadline - time.time()
        )

        if remaining <= 0:

            st.session_state.winner = (
                3 - st.session_state.player
            )

            st.session_state.phase = "finished"
            st.session_state.finish_reason = "시간 초과"

            st.rerun()

        show_timer()

        st.markdown(
            f"""
            <div class="player-label">
                Player {st.session_state.player} 차례
            </div>
            """,
            unsafe_allow_html=True
        )

        difficulty = DIFFICULTIES[
            st.session_state.level_index
        ]

        st.caption(
            f"현재 난이도: {difficulty} "
            f"({st.session_state.level_index + 1}/4)"
        )

        draw_board(9, "versus")

        show_entry(9, "versus")

        show_remaining(9)

    # -----------------------------------------------------
    # 승패
    # -----------------------------------------------------

    elif st.session_state.phase == "finished":

        st.title("대전 종료")

        st.error(
            f"Player {st.session_state.winner} 승리!"
        )

        st.write(
            f"패배 사유: Player "
            f"{3 - st.session_state.winner}의 "
            f"{st.session_state.finish_reason}"
        )

        if st.button("다시 대전하기", type="primary"):

            st.session_state.phase = "rules"
            st.session_state.page = "versus"

            st.rerun()

        if st.button("메인 화면"):

            st.session_state.page = "home"
            st.rerun()

    # -----------------------------------------------------
    # 최종 우승
    # -----------------------------------------------------

    elif st.session_state.phase == "champion":

        st.title("최종 우승")

        st.balloons()

        st.success(
            f"Player {st.session_state.winner} 최종 우승!"
        )

        st.write(
            "하, 중, 상, 최상 난이도를 모두 완료했습니다."
        )

        if st.button("다시 대전하기", type="primary"):

            st.session_state.phase = "rules"
            st.session_state.page = "versus"

            st.rerun()

        if st.button("메인 화면"):

            st.session_state.page = "home"
            st.rerun()
