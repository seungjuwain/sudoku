import random
import time
import math
import streamlit as st

st.set_page_config(
    page_title="Classic Sudoku",
    page_icon="🔢",
    layout="wide"
)

SYMBOLS = "123456789ABCDEFG"
DIFFICULTIES = ["하", "중", "상", "최상"]
CLUES = {"하": 26, "중": 23, "상": 20, "최상": 17}
MIN_CLUES = {9: 17, 16: 40}
TURN_SECONDS = 20

SEED = [
    [int(x) for x in row]
    for row in [
        "000000010", "400000000", "020000000",
        "000050407", "008000300", "001090000",
        "300400200", "050100000", "000806000"
    ]
]

# =========================================================
# CSS - 이미지(Classic Sudoku) 형식: 흰 칸 + 얇은 회색선 + 굵은 검은 구역선
# =========================================================

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding: 1rem 0.6rem;
}

div.stButton > button {
    width: 100%;
    min-height: 42px;
    font-size: 16px;
}

/* 스도쿠 판 크기 */
.st-key-sudoku_board_9 {
    width: min(100%, 540px) !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.st-key-sudoku_board_16 {
    width: min(100%, 680px) !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* 행/열 간격 제거 + 모바일에서도 가로 배치 유지 */
.st-key-sudoku_board_9 [data-testid="stVerticalBlock"],
.st-key-sudoku_board_16 [data-testid="stVerticalBlock"] {
    gap: 0 !important;
    row-gap: 0 !important;
}

.st-key-sudoku_board_9 [data-testid="stHorizontalBlock"],
.st-key-sudoku_board_16 [data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    column-gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
}

.st-key-sudoku_board_9 [data-testid="column"],
.st-key-sudoku_board_16 [data-testid="column"],
.st-key-sudoku_board_9 [data-testid="stColumn"],
.st-key-sudoku_board_16 [data-testid="stColumn"] {
    flex: 1 1 0 !important;
    width: auto !important;
    min-width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

.st-key-sudoku_board_9 [data-testid="stTextInput"],
.st-key-sudoku_board_16 [data-testid="stTextInput"],
.st-key-sudoku_board_9 [data-testid="stWidget"],
.st-key-sudoku_board_16 [data-testid="stWidget"] {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}

.st-key-sudoku_board_9 [data-testid="stTextInput"] > div,
.st-key-sudoku_board_16 [data-testid="stTextInput"] > div {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* 셀(입력창 바깥 테두리 박스): 선은 아래 draw_board 에서 칸마다 지정 */
.st-key-sudoku_board_9 [data-baseweb="input"],
.st-key-sudoku_board_16 [data-baseweb="input"] {
    background: #ffffff !important;
    border-radius: 0 !important;
    box-sizing: border-box !important;
    box-shadow: none !important;
    outline: none !important;
    width: 100% !important;
}

.st-key-sudoku_board_9 [data-baseweb="input"]:focus-within,
.st-key-sudoku_board_16 [data-baseweb="input"]:focus-within {
    background: #fff6c8 !important;
}

.st-key-sudoku_board_9 [data-baseweb="base-input"],
.st-key-sudoku_board_16 [data-baseweb="base-input"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
}

/* 입력 글자 */
.st-key-sudoku_board_9 input,
.st-key-sudoku_board_16 input {
    width: 100% !important;
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    text-align: center !important;
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    box-shadow: none !important;
    outline: none !important;
}

.st-key-sudoku_board_9 input {
    height: clamp(34px, 6.67vw, 60px) !important;
    min-height: clamp(34px, 6.67vw, 60px) !important;
    font-size: clamp(15px, 2.5vw, 23px) !important;
}

.st-key-sudoku_board_16 input {
    height: clamp(22px, 6.25vw, 42px) !important;
    min-height: clamp(22px, 6.25vw, 42px) !important;
    font-size: clamp(11px, 1.8vw, 17px) !important;
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
}

.player-label {
    text-align: center;
    font-size: 24px;
    font-weight: 800;
    margin: 8px 0;
}

.rule-card {
    padding: 16px;
    border: 1px solid #b8c8dc;
    border-radius: 10px;
    background: #f0f6ff;
    color: #24364c;
    line-height: 1.9;
}

/* 남은 숫자 */
.remaining-number {
    border: 1px solid #b5c7df;
    border-radius: 5px;
    text-align: center;
    padding: 5px 1px;
    background: #edf5ff;
    color: #28548e;
    line-height: 1.2;
}

.remaining-number .digit {
    font-size: 22px;
    font-weight: 700;
}

.remaining-number .count {
    font-size: 12px;
    margin-top: 4px;
    color: #52657d;
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


def solve_count(
    board, n, box, limit=2,
    max_nodes=300000, max_seconds=6.0
):
    count = 0
    first_solution = None
    nodes = 0
    start = time.monotonic()
    exhausted = True

    def backtrack():
        nonlocal count, first_solution, nodes, exhausted

        if count >= limit or not exhausted:
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
        values = [v for v in board[r] if v != 0]
        if len(values) != len(set(values)):
            return False, f"{r+1}행에 중복 숫자가 있습니다."

    for c in range(n):
        values = [
            board[r][c] for r in range(n)
            if board[r][c] != 0
        ]
        if len(values) != len(set(values)):
            return False, f"{c+1}열에 중복 숫자가 있습니다."

    for br in range(0, n, box):
        for bc in range(0, n, box):
            values = [
                board[r][c]
                for r in range(br, br + box)
                for c in range(bc, bc + box)
                if board[r][c] != 0
            ]
            if len(values) != len(set(values)):
                return False, "같은 구역에 중복 숫자가 있습니다."

    return True, ""


# =========================================================
# 문제 생성
# =========================================================

@st.cache_resource
def get_seed_solution():
    """기본 퍼즐의 유일해 검증은 앱 실행 후 딱 한 번만 수행한다."""
    count, solution, complete = solve_count(
        [row[:] for row in SEED], 9, 3, limit=2, max_seconds=30.0
    )

    if count != 1 or not complete:
        raise RuntimeError("기본 퍼즐의 유일해 검증에 실패했습니다.")

    return solution


def generate_puzzle(target_clues):
    seed_solution = get_seed_solution()

    def shuffled_groups():
        groups = [
            list(range(3 * i, 3 * i + 3))
            for i in range(3)
        ]
        random.shuffle(groups)
        return [
            v for group in groups
            for v in random.sample(group, 3)
        ]

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

    puzzle = transform(SEED)
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
    st.session_state.board = [row[:] for row in board]
    st.session_state.selected = None
    st.session_state.board_mode = mode

    for r in range(n):
        for c in range(n):
            value = board[r][c]
            st.session_state[f"cell_{r}_{c}"] = (
                SYMBOLS[value - 1] if value else ""
            )


# =========================================================
# 1vs1 퍼즐 생성
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

    st.session_state.locked_values = {
        (r, c): puzzle[r][c]
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] != 0
    }

    now = time.time()
    st.session_state.turn_start = now
    st.session_state.deadline = now + TURN_SECONDS
    st.session_state.phase = "active"


def finish_versus(loser, reason):
    st.session_state.winner = 3 - loser
    st.session_state.phase = "finished"
    st.session_state.finish_reason = reason


# =========================================================
# 입력 콜백
# =========================================================

def cell_changed(r, c, mode):
    key = f"cell_{r}_{c}"
    raw = str(st.session_state.get(key, "")).strip().upper()

    n = len(st.session_state.board)
    st.session_state.selected = (r, c)

    if (r, c) in st.session_state.get("locked", set()):
        original = st.session_state.locked_values[(r, c)]
        st.session_state.board[r][c] = original
        st.session_state[key] = SYMBOLS[original - 1]
        return

    if raw == "":
        if mode == "solve":
            st.session_state.board[r][c] = 0
        elif st.session_state.board[r][c] != 0:
            # 이미 채워진 칸은 지울 수 없다
            st.session_state[key] = SYMBOLS[
                st.session_state.board[r][c] - 1
            ]
        return

    allowed = SYMBOLS[:n]

    if len(raw) != 1 or raw not in allowed:
        st.session_state[key] = ""
        return

    value = SYMBOLS.index(raw) + 1

    if mode == "solve":
        st.session_state.board[r][c] = value
        st.session_state.solve_result = None
        return

    if mode == "puzzle":
        if st.session_state.game_over:
            st.session_state[key] = ""
            return

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

    if mode == "versus":
        if st.session_state.phase != "active":
            st.session_state[key] = ""
            return

        # 20초를 넘겨서 입력하면 시간 초과 패배
        if time.time() >= st.session_state.deadline:
            st.session_state[key] = ""
            finish_versus(st.session_state.player, "시간 초과")
            return

        if st.session_state.board[r][c] != 0:
            st.session_state[key] = SYMBOLS[
                st.session_state.board[r][c] - 1
            ]
            return

        # 오답이면 즉시 패배
        if value != st.session_state.solution[r][c]:
            st.session_state[key] = ""
            finish_versus(st.session_state.player, "오답")
            return

        st.session_state.board[r][c] = value

        # 판 완성 -> 다음 난이도 (마지막으로 맞힌 플레이어가 그대로 먼저 시작)
        if all(v != 0 for row in st.session_state.board for v in row):
            next_level = st.session_state.level_index + 1

            if next_level >= len(DIFFICULTIES):
                st.session_state.phase = "champion"
                st.session_state.winner = st.session_state.player
                return

            st.session_state.level_index = next_level
            make_versus_level()
            return

        # 정답 -> 상대 턴, 20초 다시 시작
        st.session_state.player = 3 - st.session_state.player
        now = time.time()
        st.session_state.turn_start = now
        st.session_state.deadline = now + TURN_SECONDS


# =========================================================
# 스도쿠 판 출력 (이미지 형식)
#  - 칸은 모두 흰색, 얇은 회색선
#  - 구역(9x9 는 3칸, 16x16 은 4칸)마다 굵은 검은 실선
#  - 칸마다 왼쪽/위쪽 선만 그려서 선이 겹쳐 두꺼워지지 않게 함
# =========================================================

THIN = "1px solid #8c8c8c"
THICK = "3px solid #111111"


def draw_board(n, mode):
    box = 3 if n == 9 else 4
    locked = st.session_state.get("locked", set())
    board = st.session_state.board

    rules = []

    for r in range(n):
        for c in range(n):
            is_given = (r, c) in locked
            has_value = board[r][c] != 0

            if is_given:
                color, weight = "#111111", "800"
            elif has_value:
                color, weight = "#1a56c4", "600"
            else:
                color, weight = "#111111", "500"

            left = THICK if c % box == 0 else THIN
            top = THICK if r % box == 0 else THIN
            right = THICK if c == n - 1 else "none"
            bottom = THICK if r == n - 1 else "none"

            sel = f"div.st-key-cell_{r}_{c}"
            rules.append(
                f"{sel} [data-baseweb='input'] {{"
                f"border-left:{left} !important;"
                f"border-top:{top} !important;"
                f"border-right:{right} !important;"
                f"border-bottom:{bottom} !important;}}"
                f"{sel} input {{"
                f"color:{color} !important;"
                f"-webkit-text-fill-color:{color} !important;"
                f"font-weight:{weight} !important;}}"
            )

    css = "<style>" + "".join(rules) + "</style>"

    with st.container(key=f"sudoku_board_{n}"):
        st.markdown(css, unsafe_allow_html=True)

        for r in range(n):
            cols = st.columns(n, gap=None)

            for c in range(n):
                key = f"cell_{r}_{c}"

                with cols[c]:
                    st.text_input(
                        f"{r+1}-{c+1}",
                        key=key,
                        max_chars=1,
                        label_visibility="collapsed",
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

    cols = st.columns(n, gap="small")

    for i, col in enumerate(cols, start=1):
        remaining = n - counts[i]

        with col:
            st.markdown(
                f"""
                <div class="remaining-number">
                    <div class="digit">{SYMBOLS[i-1]}</div>
                    <div class="count">{remaining}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# 20초 타이머 / 카운트다운
#  st_autorefresh 로 페이지 전체를 0.1초마다 다시 그리면
#  판(입력창 81개)이 그려지기도 전에 계속 새로고침되어 판이 안 뜬다.
#  -> 이 부분만 따로 갱신되는 st.fragment 를 사용한다.
# =========================================================

@st.fragment(run_every=0.2)
def timer_fragment():
    if st.session_state.phase != "active":
        return

    remaining = st.session_state.deadline - time.time()

    if remaining <= 0:
        finish_versus(st.session_state.player, "시간 초과")
        st.rerun()  # 앱 전체를 다시 실행해 결과 화면으로 이동
        return

    percent = remaining / TURN_SECONDS * 100
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
        unsafe_allow_html=True
    )


@st.fragment(run_every=0.2)
def ready_fragment():
    if st.session_state.phase != "ready":
        return

    remaining = st.session_state.ready_until - time.time()

    if remaining <= 0:
        make_versus_level()
        st.rerun()
        return

    countdown = max(1, math.ceil(remaining))

    st.markdown(
        f"""
        <div style="text-align:center;padding:35px 0;">
            <h2>1 vs 1 스도쿠 대전</h2>
            <div style="font-size:72px;font-weight:800;margin:25px 0;">
                {countdown}
            </div>
            <p style="font-size:18px;">
                잠시 후 Player {st.session_state.player}부터 시작합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


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
    "locked": set(),
    "locked_values": {},
    "board": [],
    "solution": [],
    "board_mode": "",
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
        format_func=lambda x: f"{x} × {x}",
        horizontal=True
    )

    if st.button("빈 판 만들기", type="primary"):
        prepare_board([[0] * n for _ in range(n)], "solve")

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
    st.caption("셀에 숫자를 입력하십시오. 입력한 숫자는 즉시 반영됩니다.")

    draw_board(n, "solve")
    show_remaining(n)

    if st.button("완료", type="primary"):
        board = [row[:] for row in st.session_state.board]
        box = 3 if n == 9 else 4

        clue_count = sum(v != 0 for row in board for v in row)
        valid, reason = validate(board, n, box)

        if not valid:
            st.session_state.solve_result = (
                "불가능", f"규칙 위반: {reason}"
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
                n, box, limit=2, max_seconds=6.0
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
            else:
                st.session_state.solve_result = ("가능", solution)

        st.rerun()

    result = st.session_state.solve_result

    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.warning(result[1])
        else:
            st.success("유일한 해답을 찾았습니다.")
            for row in result[1]:
                st.write("　".join(SYMBOLS[v - 1] for v in row))

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
        f"두 플레이어가 번갈아 한 칸씩 정답을 입력합니다. "
        f"한 턴은 {TURN_SECONDS}초입니다."
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
# 일반 문제 플레이
# =========================================================

elif st.session_state.page == "puzzle_play":
    st.title("스도쿠 문제")

    st.markdown(
        f"""
        <div style="text-align:center;font-size:30px;margin:10px;">
            {'❤️ ' * st.session_state.lives}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.game_over:
        st.error("실패했습니다. 목숨을 모두 사용했습니다.")
    else:
        draw_board(9, "puzzle")
        show_remaining(9)

        if all(v != 0 for row in st.session_state.board for v in row):
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
# 1vs1 대전
# =========================================================

elif st.session_state.page == "versus":
    st.title("1 vs 1 스도쿠 대전")

    if st.session_state.phase == "rules":
        st.markdown(f"""
        <div class="rule-card">
        <h3>대전 규칙</h3>
        1. Player 1부터 시작합니다.<br>
        2. 각 플레이어에게 한 턴당 {TURN_SECONDS}초가 주어집니다.<br>
        3. 제한 시간 안에 빈칸 한 개를 정확하게 채우면
        상대 플레이어에게 턴이 넘어갑니다.<br>
        4. 틀린 숫자를 입력하거나 {TURN_SECONDS}초 안에 입력하지 못하면
        해당 플레이어가 패배합니다.<br>
        5. 모든 칸을 정확하게 채우면 다음 난이도로 올라갑니다.<br>
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
        ready_fragment()

    elif st.session_state.phase == "active":
        timer_fragment()

        st.markdown(
            f"""
            <div class="player-label">
                Player {st.session_state.player} 차례
            </div>
            """,
            unsafe_allow_html=True
        )

        difficulty = DIFFICULTIES[st.session_state.level_index]

        st.caption(
            f"현재 난이도: {difficulty} "
            f"({st.session_state.level_index + 1}/4)"
        )

        draw_board(9, "versus")
        show_remaining(9)

        st.caption("정답을 입력하면 상대에게 턴이 넘어갑니다.")

    elif st.session_state.phase == "finished":
        st.title("대전 종료")

        winner = st.session_state.winner
        st.error(f"Player {winner} 승리!")

        st.write(
            f"패배 사유: Player {3-winner}의 "
            f"{st.session_state.finish_reason}"
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
            f"Player {st.session_state.winner} 최종 우승!"
        )

        st.write("하, 중, 상, 최상 모든 난이도를 완료했습니다.")

        if st.button("다시 대전하기", type="primary"):
            st.session_state.phase = "rules"
            st.session_state.page = "versus"
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()
