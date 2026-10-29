
import random
import streamlit as st

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="centered")

SYMBOLS = "123456789ABCDEFG"

# 검증된 17개 단서 스도쿠를 기반으로 문제를 생성합니다.
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

# -------------------------
# 디자인
# -------------------------
st.markdown("""
<style>
.block-container {
    max-width: 760px;
    padding: 2rem 1rem;
}
h1, h2, h3 { text-align: center; }
div.stButton > button {
    width: 100%;
    min-height: 44px;
    font-size: 17px;
}
div[data-testid="stTextInput"] {
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stTextInput"] label {
    display: none !important;
}
div[data-testid="stTextInput"] input {
    box-sizing: border-box !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    padding: 0 !important;
    text-align: center !important;
    font-size: clamp(11px, 2.4vw, 21px) !important;
    border-radius: 0 !important;
    border: 1px solid #888 !important;
    background: var(--secondary-background-color) !important;
}
div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    min-width: 0 !important;
    padding: 0 !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3n) {
    border-right: 2px solid var(--text-color);
}
.sudoku-caption {
    text-align: center;
    color: var(--text-color);
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)


# -------------------------
# 스도쿠 풀이 엔진
# -------------------------
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


def solve_count(board, n, box, limit=2):
    """해의 개수를 limit개까지만 검사하고 첫 번째 해를 반환합니다."""
    count = 0
    first_solution = None

    def backtrack():
        nonlocal count, first_solution

        if count >= limit:
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

            if count >= limit:
                return

    backtrack()
    return count, first_solution


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


# -------------------------
# 스도쿠 판 입력
# -------------------------
def reset_grid(prefix, board):
    n = len(board)
    for r in range(n):
        for c in range(n):
            key = f"{prefix}_{r}_{c}"
            value = board[r][c]
            st.session_state[key] = SYMBOLS[value - 1] if value else ""


def read_grid(prefix, n):
    board = []

    for r in range(n):
        row = []

        for c in range(n):
            raw = str(
                st.session_state.get(f"{prefix}_{r}_{c}", "")
            ).strip().upper()

            if not raw:
                row.append(0)
            elif raw in SYMBOLS[:n]:
                row.append(SYMBOLS.index(raw) + 1)
            else:
                raise ValueError(
                    f"{r + 1}행 {c + 1}열의 값이 잘못되었습니다. "
                    f"허용되는 값: {SYMBOLS[:n]}"
                )

        board.append(row)

    return board


def draw_grid(prefix, n, box, locked=None):
    locked = locked or set()

    # 정사각형에 가까운 판을 만들기 위해 규격별 셀 높이를 조정합니다.
    cell_height = 48 if n == 9 else 34

    for r in range(n):
        cols = st.columns(n, gap=None)

        for c in range(n):
            key = f"{prefix}_{r}_{c}"

            with cols[c]:
                st.markdown(
                    f"""<div style="height:{cell_height}px;
                    display:none"></div>""",
                    unsafe_allow_html=True,
                )

                st.text_input(
                    f"셀 {r + 1}-{c + 1}",
                    key=key,
                    max_chars=1,
                    label_visibility="collapsed",
                    disabled=(r, c) in locked,
                    placeholder="",
                )

        # 구역 경계: 9×9는 3행마다, 16×16은 4행마다 표시합니다.
        if (r + 1) % box == 0 and r != n - 1:
            st.markdown(
                f"""<div style="height:2px;
                background:var(--text-color);
                margin:0;padding:0"></div>""",
                unsafe_allow_html=True,
            )


# -------------------------
# 문제 생성
# -------------------------
def transform_seed(puzzle, solution):
    """행·열·숫자 치환으로 문제를 무작위 변형합니다."""
    def permute_groups():
        groups = [list(range(3 * i, 3 * i + 3)) for i in range(3)]
        random.shuffle(groups)
        return [v for group in groups for v in random.sample(group, 3)]

    rows = permute_groups()
    cols = permute_groups()
    digits = list(range(1, 10))
    random.shuffle(digits)
    mapping = {i + 1: digits[i] for i in range(9)}

    transpose = random.choice([False, True])

    def transform(board):
        result = [[board[r][c] for c in cols] for r in rows]

        if transpose:
            result = [list(row) for row in zip(*result)]

        return [
            [mapping[v] if v else 0 for v in row]
            for row in result
        ]

    return transform(puzzle), transform(solution)


def generate_puzzle(target_clues):
    seed_board = [
        [int(ch) for ch in SEED[r * 9:(r + 1) * 9]]
        for r in range(9)
    ]

    count, seed_solution = solve_count(
        [row[:] for row in seed_board], 9, 3, limit=2
    )

    if count != 1:
        raise RuntimeError("기본 퍼즐의 유일해 검증에 실패했습니다.")

    puzzle, solution = transform_seed(seed_board, seed_solution)

    # 17개 단서에서 시작해 목표 단서 수까지 정답 숫자를 공개합니다.
    empty_cells = [
        (r, c)
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] == 0
    ]
    random.shuffle(empty_cells)

    add_count = target_clues - 17

    for r, c in empty_cells[:add_count]:
        puzzle[r][c] = solution[r][c]

    actual_clues = sum(v != 0 for row in puzzle for v in row)

    if actual_clues != target_clues:
        raise RuntimeError("목표 단서 개수와 일치하지 않습니다.")

    return puzzle, solution


# -------------------------
# 세션 초기화
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "solve_result" not in st.session_state:
    st.session_state.solve_result = None

if "play_feedback" not in st.session_state:
    st.session_state.play_feedback = None


# -------------------------
# 첫 화면
# -------------------------
if st.session_state.page == "home":
    st.title("스도쿠")

    left, right = st.columns(2)

    with left:
        if st.button("풀이", type="primary"):
            st.session_state.page = "solve_select"
            st.rerun()

    with right:
        if st.button("문제", type="primary"):
            st.session_state.page = "puzzle_select"
            st.rerun()


# -------------------------
# 풀이 규격 선택
# -------------------------
elif st.session_state.page == "solve_select":
    st.title("스도쿠 풀이")

    n = st.radio(
        "규격 선택",
        [9, 16],
        format_func=lambda x: f"{x} × {x}",
        horizontal=True,
    )

    if st.button("빈 스도쿠 판 만들기", type="primary"):
        prefix = f"solve_{n}"
        reset_grid(prefix, [[0] * n for _ in range(n)])

        st.session_state.solve_n = n
        st.session_state.solve_prefix = prefix
        st.session_state.solve_result = None
        st.session_state.page = "solve_board"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# -------------------------
# 풀이 입력 및 결과
# -------------------------
elif st.session_state.page == "solve_board":
    n = st.session_state.solve_n
    box = 3 if n == 9 else 4
    prefix = st.session_state.solve_prefix

    st.title(f"{n} × {n} 스도쿠")
    st.caption("빈칸에 숫자를 입력한 후 완료를 누르십시오.")
    if n == 16:
        st.caption("16×16에서는 1~9와 A~G를 사용합니다.")

    draw_grid(prefix, n, box)

    if st.button("완료", type="primary"):
        # 중요: 이전 결과를 먼저 지우고 현재 위젯 값을 다시 읽습니다.
        st.session_state.solve_result = None

        try:
            current_board = read_grid(prefix, n)
            valid, reason = validate(current_board, n, box)

            if not valid:
                st.session_state.solve_result = ("불가능", reason)
            else:
                count, solution = solve_count(
                    [row[:] for row in current_board],
                    n,
                    box,
                    limit=1,
                )

                if count == 0 or solution is None:
                    st.session_state.solve_result = (
                        "불가능",
                        "입력한 숫자와 스도쿠 규칙을 만족하는 해가 없습니다.",
                    )
                else:
                    st.session_state.solve_result = ("가능", solution)

        except ValueError as error:
            st.session_state.solve_result = ("불가능", str(error))

        st.rerun()

    result = st.session_state.solve_result

    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.write(f"사유: {result[1]}")
        else:
            st.success("풀이 완료")
            solution = result[1]

            # 표 형식으로 완성판을 표시합니다.
            for row in solution:
                st.code(
                    "  ".join(SYMBOLS[v - 1] for v in row),
                    language=None,
                )

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# -------------------------
# 문제 난이도 선택
# -------------------------
elif st.session_state.page == "puzzle_select":
    st.title("스도쿠 문제")

    clue_map = {
        "하": 26,
        "중": 23,
        "상": 20,
        "최상": 17,
    }

    difficulty = st.radio(
        "난이도 선택",
        ["하", "중", "상", "최상"],
        horizontal=True,
    )

    st.write(f"초기 단서 개수: {clue_map[difficulty]}개")

    if st.button("문제 생성", type="primary"):
        try:
            puzzle, solution = generate_puzzle(clue_map[difficulty])

            st.session_state.puzzle = puzzle
            st.session_state.solution = solution
            st.session_state.difficulty = difficulty
            st.session_state.puzzle_locked = {
                (r, c)
                for r in range(9)
                for c in range(9)
                if puzzle[r][c] != 0
            }

            reset_grid("play", puzzle)
            st.session_state.play_feedback = None
            st.session_state.page = "puzzle_play"
            st.rerun()

        except RuntimeError as error:
            st.error(str(error))

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# -------------------------
# 문제 풀이 화면
# -------------------------
elif st.session_state.page == "puzzle_play":
    st.title(f"스도쿠 — {st.session_state.difficulty}")

    st.caption(
        "초기 단서 "
        + str(sum(v != 0 for row in st.session_state.puzzle for v in row))
        + "개 · 주어진 숫자는 수정할 수 없습니다."
    )

    draw_grid(
        "play",
        9,
        3,
        locked=st.session_state.puzzle_locked,
    )

    if st.button("정답 확인", type="primary"):
        try:
            board = read_grid("play", 9)
            valid, reason = validate(board, 9, 3)

            if not valid:
                st.session_state.play_feedback = ("error", reason)
            elif any(v == 0 for row in board for v in row):
                st.session_state.play_feedback = (
                    "warning",
                    "아직 빈칸이 있습니다.",
                )
            elif board == st.session_state.solution:
                st.session_state.play_feedback = (
                    "success",
                    "정답입니다!",
                )
            else:
                st.session_state.play_feedback = (
                    "error",
                    "정답이 아닙니다. 숫자를 다시 확인하십시오.",
                )

        except ValueError as error:
            st.session_state.play_feedback = ("error", str(error))

        st.rerun()

    feedback = st.session_state.play_feedback

    if feedback:
        if feedback[0] == "success":
            st.success(feedback[1])
        elif feedback[0] == "warning":
            st.warning(feedback[1])
        else:
            st.error(feedback[1])

    left, right = st.columns(2)

    with left:
        if st.button("새 문제"):
            st.session_state.page = "puzzle_select"
            st.rerun()

    with right:
        if st.button("처음으로"):
            st.session_state.page = "home"
            st.rerun()
