import random
import time
import math
import streamlit as st
import streamlit.components.v1 as components

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
# CSS
# =========================================================

st.markdown("""
<style>

.block-container {
    max-width: 1100px;
    padding: 1rem 0.6rem;
}

/* 기본 버튼 */

div.stButton > button {
    width: 100%;
    min-height: 42px;
    font-size: 16px;
}

/* 스도쿠 판 컨테이너 */

.st-key-sudoku_board_9 {
    width: min(100%, 540px) !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.st-key-sudoku_board_16 {
    width: min(100%, 640px) !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* 행 사이 간격 제거 */

.st-key-sudoku_board_9 [data-testid="stVerticalBlock"],
.st-key-sudoku_board_16 [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

/* 열 사이 간격 제거 */

.st-key-sudoku_board_9 [data-testid="stHorizontalBlock"],
.st-key-sudoku_board_16 [data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}

/* 셀 입력 영역 */

.st-key-sudoku_board_9 [data-testid="stTextInput"],
.st-key-sudoku_board_16 [data-testid="stTextInput"] {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}

.st-key-sudoku_board_9 [data-testid="stTextInput"] > div,
.st-key-sudoku_board_16 [data-testid="stTextInput"] > div {
    width: 100% !important;
}

/* 9x9 정사각형 셀 */

.st-key-sudoku_board_9 input {
    width: 100% !important;
    height: clamp(34px, 6.67vw, 60px) !important;
    min-height: clamp(34px, 6.67vw, 60px) !important;
    border-radius: 0 !important;
    font-size: clamp(15px, 2.5vw, 23px) !important;
    text-align: center !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}

/* 16x16 정사각형 셀 */

.st-key-sudoku_board_16 input {
    width: 100% !important;
    height: clamp(22px, 6.25vw, 40px) !important;
    min-height: clamp(22px, 6.25vw, 40px) !important;
    border-radius: 0 !important;
    font-size: clamp(11px, 1.8vw, 16px) !important;
    text-align: center !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}

/* 입력창 기본 스타일 */

.st-key-sudoku_board_9 input,
.st-key-sudoku_board_16 input {
    box-shadow: none !important;
    outline: none !important;
}

/* 타이머 */

.timer-outer {
    width: 100%;
    height: 18px;
    background: #dedede;
    border-radius: 10px;
    overflow: hidden;
    margin: 8px 0 12px 0;
}

.timer-inner {
    height: 100%;
    border-radius: 10px;
    transition: width 0.12s linear;
}

/* 플레이어 */

.player-label {
    text-align: center;
    font-size: 24px;
    font-weight: 800;
    margin: 8px 0;
}

/* 룰 설명 */

.rule-card {
    padding: 16px;
    border: 1px solid #b8c8dc;
    border-radius: 10px;
    background: #f0f6ff;
    color: #24364c;
    line-height: 1.9;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 스도쿠 풀이 엔진
# =========================================================

def candidates(board, r, c, n, box):

    used = set(board[r])

    used.update(
        board[i][c]
        for i in range(n)
    )

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

            options = candidates(
                board, r, c, n, box
            )

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
    max_seconds=6.0
):

    count = 0
    first_solution = None

    nodes = 0
    start = time.monotonic()

    exhausted = True

    def backtrack():

        nonlocal count
        nonlocal first_solution
        nonlocal nodes
        nonlocal exhausted

        if count >= limit:
            return

        nodes += 1

        if (
            nodes > max_nodes
            or time.monotonic() - start > max_seconds
        ):

            exhausted = False
            return

        r, c, options = find_empty(
            board, n, box
        )

        if r is None:

            count += 1

            if first_solution is None:
                first_solution = [
                    row[:] for row in board
                ]

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

        values = [
            v for v in board[r]
            if v != 0
        ]

        if len(values) != len(set(values)):

            return (
                False,
                f"{r + 1}행에 중복 숫자가 있습니다."
            )

    for c in range(n):

        values = [
            board[r][c]
            for r in range(n)
            if board[r][c] != 0
        ]

        if len(values) != len(set(values)):

            return (
                False,
                f"{c + 1}열에 중복 숫자가 있습니다."
            )

    for br in range(0, n, box):

        for bc in range(0, n, box):

            values = [
                board[r][c]
                for r in range(br, br + box)
                for c in range(bc, bc + box)
                if board[r][c] != 0
            ]

            if len(values) != len(set(values)):

                return (
                    False,
                    "같은 구역에 중복 숫자가 있습니다."
                )

    return True, ""


# =========================================================
# 문제 생성
# =========================================================

def generate_puzzle(target_clues):

    seed = [
        [
            int(x)
            for x in SEED[r * 9:(r + 1) * 9]
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
        raise RuntimeError(
            "기본 퍼즐의 유일해 검증에 실패했습니다."
        )

    def shuffled_groups():

        groups = [
            list(range(3 * i, 3 * i + 3))
            for i in range(3)
        ]

        random.shuffle(groups)

        return [
            v
            for group in groups
            for v in random.sample(group, 3)
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

            result = [
                list(row)
                for row in zip(*result)
            ]

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

    assert sum(
        v != 0
        for row in puzzle
        for v in row
    ) == target_clues

    return puzzle, solution


# =========================================================
# 입력 상태 초기화
# =========================================================

def clear_cell_keys():

    for r in range(16):

        for c in range(16):

            key = f"cell_{r}_{c}"

            if key in st.session_state:
                del st.session_state[key]


def prepare_board(board, mode):

    clear_cell_keys()

    n = len(board)

    st.session_state.board = [
        row[:] for row in board
    ]

    st.session_state.selected = None

    st.session_state.board_mode = mode

    for r in range(n):

        for c in range(n):

            value = board[r][c]

            st.session_state[
                f"cell_{r}_{c}"
            ] = (
                SYMBOLS[value - 1] if value else ""
            )


# =========================================================
# 입력 콜백
# =========================================================

def cell_changed(r, c, mode):

    key = f"cell_{r}_{c}"

    raw = str(
        st.session_state.get(key, "")
    ).strip().upper()

    n = len(st.session_state.board)

    st.session_state.selected = (r, c)

    # 초기 단서는 수정 불가
    if (r, c) in st.session_state.get("locked", set()):

        original = st.session_state.locked_values[(r, c)]

        st.session_state.board[r][c] = original

        st.session_state[key] = SYMBOLS[original - 1]

        return

    # 빈칸 입력
    if raw == "":

        if mode == "solve":
            st.session_state.board[r][c] = 0

        return

    allowed = SYMBOLS[:n]

    # 한 글자 숫자 또는 기호만 허용
    if len(raw) != 1 or raw not in allowed:

        st.session_state[key] = ""
        return

    value = SYMBOLS.index(raw) + 1

    # 풀이 모드
    if mode == "solve":

        st.session_state.board[r][c] = value
        st.session_state.solve_result = None

        return

    # 일반 문제 모드
    if mode == "puzzle":

        if st.session_state.board[r][c] != 0:

            st.session_state[key] = SYMBOLS[
                st.session_state.board[r][c] - 1
            ]

            return

        if value == st.session_state.solution[r][c]:

            st.session_state.board[r][c] = value

        else:

            st.session_state.board[r][c] = 0
            st.session_state[key] = ""

            st.session_state.lives -= 1

            if st.session_state.lives <= 0:

                st.session_state.lives = 0
                st.session_state.game_over = True

        return

    # 1vs1 모드
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

        if st.session_state.board[r][c] != 0:

            st.session_state[key] = SYMBOLS[
                st.session_state.board[r][c] - 1
            ]

            return

        # 오답
        if value != st.session_state.solution[r][c]:

            st.session_state.winner = (
                2 if st.session_state.player == 1 else 1
            )

            st.session_state.phase = "finished"
            st.session_state.finish_reason = "오답"

            st.session_state[key] = ""

            return

        # 정답
        st.session_state.board[r][c] = value

        # 모든 칸 완료 여부
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

            st.session_state.level_index = next_level

            # 마지막 정답자가 다음 난이도도 시작
            make_versus_level()

            return

        # 상대에게 턴 넘기기
        st.session_state.player = (
            2 if st.session_state.player == 1 else 1
        )

        st.session_state.turn_start = time.time()
        st.session_state.deadline = time.time() + 20


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

    prepare_board(
        puzzle,
        "versus"
    )

    st.session_state.solution = solution

    st.session_state.locked = {
        (r, c)
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] != 0
    }

    st.session_state.locked_values = {
        (r, c): puzzle[r][c]
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] != 0
    }

    now = time.time()

    st.session_state.turn_start = now
    st.session_state.deadline = now + 20

    st.session_state.phase = "active"


# =========================================================
# 스도쿠 판 출력
# =========================================================

def draw_board(n, mode):

    box = 3 if n == 9 else 4

    selected = st.session_state.get("selected")

    locked = st.session_state.get("locked", set())

    # 모든 셀 스타일을 한 번에 생성
    css = "<style>"

    for r in range(n):

        for c in range(n):

            key = f"cell_{r}_{c}"

            is_selected = selected == (r, c)

            is_given = (r, c) in locked

            in_same_area = (
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
                background = "#e8dcff"

            elif in_same_area:
                background = "#dceeff"

            elif is_given:
                background = "#e9eef5"

            else:
                background = "#ffffff"

            color = (
                "#254f91"
                if is_given
                else "#222222"
            )

            left = (
                "3px solid #222222"
                if c % box == 0
                else "1px solid #aaaaaa"
            )

            top = (
                "3px solid #222222"
                if r % box == 0
                else "1px solid #aaaaaa"
            )

            right = (
                "3px solid #222222"
                if (c + 1) % box == 0
                else "1px solid #aaaaaa"
            )

            bottom = (
                "3px solid #222222"
                if (r + 1) % box == 0
                else "1px solid #aaaaaa"
            )

            css += f"""
            div.st-key-{key} input {{
                background: {background} !important;
                color: {color} !important;
                border-left: {left} !important;
                border-top: {top} !important;
                border-right: {right} !important;
                border-bottom: {bottom} !important;
                border-radius: 0 !important;
                font-weight: {'700' if is_given else '500'} !important;
            }}
            """

    css += "</style>"

    with st.container(key=f"sudoku_board_{n}"):

        st.markdown(
            css,
            unsafe_allow_html=True
        )

        for r in range(n):

            cols = st.columns(
                n,
                gap=None
            )

            for c in range(n):

                key = f"cell_{r}_{c}"

                with cols[c]:

                    st.text_input(
                        f"{r+1}-{c+1}",
                        key=key,
                        max_chars=1,
                        label_visibility="collapsed",
                        disabled=False,
                        on_change=cell_changed,
                        args=(r, c, mode)
                    )


# =========================================================
# 숫자별 남은 개수
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

    cols = st.columns(
        n,
        gap="small"
    )

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
                    ">
                        {SYMBOLS[i-1]}
                    </div>

                    <div style="
                        font-size:12px;
                        margin-top:4px;
                        color:#52657d;
                    ">
                        {remaining}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# 20초 타이머
# =========================================================

def show_timer():

    remaining = max(
        0,
        st.session_state.deadline - time.time()
    )

    percent = remaining / 20 * 100

    color = (
        "#e44b4b"
        if remaining <= 5
        else "#4285d4"
    )

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
                 style="
                    width:{percent}%;
                    background:{color};
                 ">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    return remaining


# =========================================================
# 세션 상태
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
    "selected": None,
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 홈 화면
# =========================================================

if st.session_state.page == "home":

    st.title("Classic Sudoku")

    a, b = st.columns(2)

    with a:

        if st.button(
            "풀이",
            type="primary"
        ):

            st.session_state.page = "solve_select"
            st.rerun()

    with b:

        if st.button(
            "문제",
            type="primary"
        ):

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
        format_func=lambda x: f"{x} × {x}",
        horizontal=True
    )

    if st.button(
        "빈 판 만들기",
        type="primary"
    ):

        prepare_board(
            [[0] * n for _ in range(n)],
            "solve"
        )

        st.session_state.solve_n = n
        st.session_state.solve_result = None
        st.session_state.locked = set()
        st.session_state.locked_values = {}

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
        "셀에 숫자를 입력하십시오. "
        "입력한 숫자는 즉시 반영됩니다."
    )

    draw_board(n, "solve")

    show_remaining(n)

    if st.button(
        "완료",
        type="primary"
    ):

        board = [
            row[:]
            for row in st.session_state.board
        ]

        box = 3 if n == 9 else 4

        clue_count = sum(
            v != 0
            for row in board
            for v in row
        )

        valid, reason = validate(
            board,
            n,
            box
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
                f"최소 {MIN_CLUES[n]}개 이상의 단서가 필요합니다."
            )

        else:

            count, solution, complete = solve_count(
                [row[:] for row in board],
                n,
                box,
                limit=2,
                max_seconds=6.0
            )

            if not complete:

                st.session_state.solve_result = (
                    "불가능",
                    "풀이 검증 시간 초과: 단서를 더 입력한 후 다시 시도해 주십시오."
                )

            elif count == 0:

                st.session_state.solve_result = (
                    "불가능",
                    "규칙 위반: 입력한 단서로는 해답을 만들 수 없습니다."
                )

            elif count >= 2:

                st.session_state.solve_result = (
                    "불가능",
                    "단서 부족: 가능한 해답이 여러 개입니다."
                )

            elif count == 1:

                st.session_state.solve_result = (
                    "가능",
                    solution
                )

        st.rerun()

    result = st.session_state.solve_result

    if result:

        if result[0] == "불가능":

            st.error("풀이 불가능")

            st.warning(result[1])

        else:

            st.success("유일한 해답을 찾았습니다.")

            solution = result[1]

            for row in solution:

                st.write(
                    "　".join(
                        SYMBOLS[v - 1]
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

    if st.button(
        "문제 생성",
        type="primary"
    ):

        puzzle, solution = generate_puzzle(
            CLUES[difficulty]
        )

        prepare_board(
            puzzle,
            "puzzle"
        )

        st.session_state.solution = solution

        st.session_state.locked = {
            (r, c)
            for r in range(9)
            for c in range(9)
            if puzzle[r][c] != 0
        }

        st.session_state.locked_values = {
            (r, c): puzzle[r][c]
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
        "두 플레이어가 번갈아 한 칸씩 정답을 입력합니다."
    )

    if st.button(
        "1 vs 1 시작",
        type="primary"
    ):

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
# 일반 문제 플레이
# =========================================================

elif st.session_state.page == "puzzle_play":

    st.title("스도쿠 문제")

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:30px;
            margin:10px;
        ">
            {'❤️ ' * st.session_state.lives}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.game_over:

        st.error(
            "실패했습니다. 목숨을 모두 사용했습니다."
        )

    else:

        draw_board(9, "puzzle")

        show_remaining(9)

        if all(
            v != 0
            for row in st.session_state.board
            for v in row
        ):

            if (
                st.session_state.board
                == st.session_state.solution
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

        2. 각 플레이어에게 한 턴당 20초가 주어집니다.<br>

        3. 제한 시간 안에 빈칸 한 개를 정확하게 채우면
        상대 플레이어에게 턴이 넘어갑니다.<br>

        4. 틀린 숫자를 입력하거나 20초 안에 입력하지 못하면
        해당 플레이어가 패배합니다.<br>

        5. 모든 칸을 정확하게 채우면 다음 난이도로 올라갑니다.<br>

        6. 난이도는 하 → 중 → 상 → 최상 순서입니다.<br>

        7. 다음 난이도에서도 마지막으로 성공한 플레이어가
        먼저 시작합니다.

        </div>
        """, unsafe_allow_html=True)

        st.write("첫 번째 판은 하 난이도입니다.")

        if st.button(
            "대전 시작",
            type="primary"
        ):

            st.session_state.level_index = 0
            st.session_state.player = 1

            st.session_state.phase = "ready"

            st.session_state.ready_until = (
                time.time() + 3
            )

            st.rerun()

    # -----------------------------------------------------
    # 카운트다운
    # -----------------------------------------------------

    elif st.session_state.phase == "ready":

        st_autorefresh(
            interval=100,
            key="versus_ready_countdown"
        )

        remaining = (
            st.session_state.ready_until
            - time.time()
        )

        if remaining <= 0:

            # 카운트다운 종료 시 퍼즐 생성
            make_versus_level()

            # active 상태를 확인한 후 다시 렌더링
            st.session_state.phase = "active"

            st.rerun()

        else:

            countdown = max(
                1,
                math.ceil(remaining)
            )

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    padding:35px 0;
                ">

                    <h2>1 vs 1 스도쿠 대전</h2>

                    <div style="
                        font-size:72px;
                        font-weight:800;
                        margin:25px 0;
                    ">
                        {countdown}
                    </div>

                    <p style="font-size:18px;">
                        잠시 후 Player 1부터 시작합니다.
                    </p>

                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # 실제 대전
    # -----------------------------------------------------

    elif st.session_state.phase == "active":

        st_autorefresh(
            interval=100,
            key="versus_active_timer"
        )

        # 제한 시간 확인
        remaining = (
            st.session_state.deadline
            - time.time()
        )

        if remaining <= 0:

            st.session_state.winner = (
                2 if st.session_state.player == 1 else 1
            )

            st.session_state.phase = "finished"

            st.session_state.finish_reason = "시간 초과"

            st.rerun()

        # 타이머
        show_timer()

        # 플레이어
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

        # 타이머 바로 아래에 스도쿠 판
        draw_board(9, "versus")

        show_remaining(9)

        st.caption(
            "정답을 입력하면 상대에게 턴이 넘어갑니다."
        )

    # -----------------------------------------------------
    # 패배 및 승리
    # -----------------------------------------------------

    elif st.session_state.phase == "finished":

        st.title("대전 종료")

        winner = st.session_state.winner

        st.error(
            f"Player {winner} 승리!"
        )

        st.write(
            f"패배 사유: Player {3 - winner}의 "
            f"{st.session_state.finish_reason}"
        )

        if st.button(
            "다시 대전하기",
            type="primary"
        ):

            st.session_state.phase = "rules"
            st.session_state.page = "versus"
            st.session_state.winner = None

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
            f"Player {st.session_state.winner} "
            "최종 우승!"
        )

        st.write(
            "하, 중, 상, 최상 모든 난이도를 완료했습니다."
        )

        if st.button(
            "다시 대전하기",
            type="primary"
        ):

            st.session_state.phase = "rules"
            st.session_state.page = "versus"
            st.rerun()

        if st.button("메인 화면"):

            st.session_state.page = "home"
            st.rerun()
