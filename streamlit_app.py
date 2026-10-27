import random
import streamlit as st

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="centered")

SYMBOLS = "123456789ABCDEFG"

# ---------------------------------------------------------
# CSS: 구역(Box) 단위 흰색 배경 및 직선 테두리 적용
# ---------------------------------------------------------
st.markdown("""
<style>
.block-container {
    max-width: 500px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}

/* 3x3 구역 컨테이너: 흰색 바탕 + 검은색 굵은 실선 테두리 */
.sudoku-box {
    background-color: #ffffff !important;
    border: 2px solid #000000 !important;
    margin: 0 !important;
    padding: 0 !important;
    box-sizing: border-box !important;
}

/* Streamlit 레이아웃 간격 제거 */
div[data-testid="stHorizontalBlock"] {
    gap: 0px !important;
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="column"] {
    padding: 0 !important;
    margin: 0 !important;
    min-width: 0 !important;
}

div[data-testid="stTextInput"] {
    margin: 0 !important;
    padding: 0 !important;
}

div[data-testid="stTextInput"] label {
    display: none !important;
}

/* 셀 내부 입력창: 회색 실선 구분 + 흰색 배경 + 직각 모서리 */
div[data-testid="stTextInput"] input {
    text-align: center !important;
    font-size: 20px !important;
    font-weight: bold !important;
    aspect-ratio: 1 / 1 !important;
    height: 100% !important;
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 0px !important;
    border: 1px solid #d0d0d0 !important; /* 내부 회색 실선 */
    background-color: #ffffff !important;
    color: #111111 !important;
    box-sizing: border-box !important;
    box-shadow: none !important;
}

div[data-testid="stTextInput"] input:focus {
    border: 2px solid #2878d0 !important;
    outline: none !important;
}

div[data-testid="stTextInput"] input:disabled {
    background-color: #f2f4f7 !important;
    color: #000000 !important;
    font-weight: 900 !important;
}

.stButton > button {
    border-radius: 6px;
    font-weight: 600;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)


def empty_board(n):
    return [["" for _ in range(n)] for _ in range(n)]


def valid(board, r, c, value, n, box):
    for i in range(n):
        if i != c and board[r][i] == value:
            return False
        if i != r and board[i][c] == value:
            return False

    br = (r // box) * box
    bc = (c // box) * box
    for rr in range(br, br + box):
        for cc in range(bc, bc + box):
            if (rr, cc) != (r, c) and board[rr][cc] == value:
                return False
    return True


def candidates(board, r, c, n, box):
    used = set(board[r])
    used.update(board[i][c] for i in range(n))
    br = (r // box) * box
    bc = (c // box) * box
    for rr in range(br, br + box):
        for cc in range(bc, bc + box):
            used.add(board[rr][cc])
    return [s for s in SYMBOLS[:n] if s not in used]


def solve_board(board, n, box):
    board = [row[:] for row in board]

    def backtrack():
        best = None
        best_options = None

        for r in range(n):
            for c in range(n):
                if board[r][c] == "":
                    opts = candidates(board, r, c, n, box)
                    if not opts:
                        return False
                    if best_options is None or len(opts) < len(best_options):
                        best = (r, c)
                        best_options = opts

        if best is None:
            return True

        r, c = best
        random.shuffle(best_options)
        for value in best_options:
            board[r][c] = value
            if backtrack():
                return True
            board[r][c] = ""
        return False

    if backtrack():
        return board
    return None


def count_solutions(board, n, box, limit=2):
    board = [row[:] for row in board]
    count = 0

    def backtrack():
        nonlocal count
        if count >= limit:
            return

        best = None
        best_options = None
        for r in range(n):
            for c in range(n):
                if board[r][c] == "":
                    opts = candidates(board, r, c, n, box)
                    if not opts:
                        return
                    if best_options is None or len(opts) < len(best_options):
                        best = (r, c)
                        best_options = opts

        if best is None:
            count += 1
            return

        r, c = best
        for value in best_options:
            board[r][c] = value
            backtrack()
            board[r][c] = ""
            if count >= limit:
                return

    backtrack()
    return count


def make_puzzle(clues):
    n = 9
    box = 3
    solution = solve_board(empty_board(n), n, box)
    puzzle = [row[:] for row in solution]

    cells = [(r, c) for r in range(n) for c in range(n)]
    random.shuffle(cells)
    removed = 0

    for r, c in cells:
        if 81 - removed <= clues:
            break
        old = puzzle[r][c]
        puzzle[r][c] = ""
        if count_solutions(puzzle, n, box) == 1:
            removed += 1
        else:
            puzzle[r][c] = old

    return puzzle, solution


def read_board(n):
    board = []
    for r in range(n):
        row = []
        for c in range(n):
            key = f"cell_{n}_{r}_{c}"
            value = st.session_state.get(key, "")
            value = str(value).strip().upper()
            row.append(value)
        board.append(row)
    return board


def set_board(board, n):
    for r in range(n):
        for c in range(n):
            st.session_state[f"cell_{n}_{r}_{c}"] = board[r][c]


def draw_board(n, box, fixed=None):
    fixed = fixed or set()

    # 3x3 (또는 4x4) 박스 단위로 큰 구역 상자를 만듭니다.
    num_boxes = n // box
    for br in range(num_boxes):
        box_cols = st.columns(num_boxes)
        for bc in range(num_boxes):
            with box_cols[bc]:
                # 3x3 흰 바탕 & 검은 실선 구역
                st.markdown('<div class="sudoku-box">', unsafe_allow_html=True)
                for lr in range(box):
                    cell_cols = st.columns(box)
                    for lc in range(box):
                        r = br * box + lr
                        c = bc * box + lc
                        key = f"cell_{n}_{r}_{c}"

                        with cell_cols[lc]:
                            st.text_input(
                                f"{r}-{c}",
                                key=key,
                                max_chars=1,
                                disabled=(r, c) in fixed,
                            )
                st.markdown('</div>', unsafe_allow_html=True)


def board_errors(board, n, box):
    errors = []
    symbols = set(SYMBOLS[:n])

    for r in range(n):
        seen = set()
        for c in range(n):
            value = board[r][c]
            if value == "":
                continue
            if value not in symbols:
                errors.append(f"{r + 1}행 {c + 1}열: 허용되지 않는 기호입니다.")
            elif value in seen:
                errors.append(f"{r + 1}행에 같은 숫자가 중복됩니다.")
            seen.add(value)

    for c in range(n):
        seen = set()
        for r in range(n):
            value = board[r][c]
            if value == "":
                continue
            if value in seen:
                errors.append(f"{c + 1}열에 같은 숫자가 중복됩니다.")
            seen.add(value)

    for br in range(0, n, box):
        for bc in range(0, n, box):
            seen = set()
            for r in range(br, br + box):
                for c in range(bc, bc + box):
                    value = board[r][c]
                    if value == "":
                        continue
                    if value in seen:
                        errors.append(
                            f"{br + 1}~{br + box}행, "
                            f"{bc + 1}~{bc + box}열 구역에 중복이 있습니다."
                        )
                    seen.add(value)

    return list(dict.fromkeys(errors))


if "mode" not in st.session_state:
    st.session_state.mode = "처음 화면"

st.title("🔢 스도쿠")
st.caption("숫자를 입력하고, 규칙에 맞는 해답을 찾아보세요.")

if st.session_state.mode == "처음 화면":
    st.write("원하시는 기능을 선택해 주세요.")
    left, right = st.columns(2)
    with left:
        st.subheader("✏️ 풀이")
        st.write("직접 입력한 스도쿠 문제의 해답을 찾습니다.")
        if st.button("풀이 시작", use_container_width=True):
            st.session_state.mode = "풀이"
            st.rerun()
    with right:
        st.subheader("🧩 문제")
        st.write("난이도를 선택해 새 문제를 풀어봅니다.")
        if st.button("문제 선택", use_container_width=True):
            st.session_state.mode = "문제"
            st.rerun()

else:
    if st.button("← 처음 화면으로"):
        st.session_state.mode = "처음 화면"
        st.rerun()

    if st.session_state.mode == "풀이":
        st.header("풀이")
        size = st.radio(
            "판 크기",
            [9, 16],
            format_func=lambda x: f"{x}×{x}",
            horizontal=True,
            key="solve_size",
        )
        n = size
        box = 3 if n == 9 else 4

        if st.button("빈 판으로 초기화"):
            for r in range(n):
                for c in range(n):
                    st.session_state[f"cell_{n}_{r}_{c}"] = ""
            st.session_state.pop("solve_result", None)
            st.rerun()

        st.info("빈칸에 숫자를 입력하세요. 9×9는 1-9, 16×16은 1-9와 A-G를 사용합니다.")
        
        draw_board(n, box)

        if st.button("완료 — 풀이하기", type="primary", use_container_width=True):
            board = read_board(n)
            errors = board_errors(board, n, box)

            if errors:
                st.error("입력한 판에 규칙 위반이 있습니다.")
                for err in errors[:8]:
                    st.write(f"• {err}")
            else:
                result = solve_board(board, n, box)
                if result is None:
                    st.error("풀이 불가능: 입력한 조건으로는 해답을 찾을 수 없습니다.")
                else:
                    set_board(result, n)
                    st.success("풀이가 완료되었습니다.")
                    st.rerun()

    elif st.session_state.mode == "문제":
        st.header("문제 선택")
        difficulty = st.radio(
            "난이도",
            ["하", "중", "상", "최상"],
            horizontal=True,
        )
        clue_counts = {"하": 26, "중": 23, "상": 20, "최상": 17}
        st.caption(f"선택한 난이도: {difficulty} · 목표 숫자 수: {clue_counts[difficulty]}개")

        if st.button("새 문제 만들기", type="primary", use_container_width=True):
            with st.spinner("문제를 만드는 중입니다..."):
                puzzle, solution = make_puzzle(clue_counts[difficulty])
            st.session_state.puzzle = puzzle
            st.session_state.solution = solution
            st.session_state.puzzle_fixed = {
                (r, c)
                for r in range(9)
                for c in range(9)
                if puzzle[r][c] != ""
            }
            set_board(puzzle, 9)
            st.session_state.puzzle_message = ""
            st.rerun()

        if "puzzle" in st.session_state:
            st.write("빈칸에 숫자를 입력해 문제를 풀어보세요.")
            
            draw_board(9, 3, st.session_state.puzzle_fixed)

            left, right = st.columns(2)
            with left:
                if st.button("정답 확인", use_container_width=True):
                    board = read_board(9)
                    if board == st.session_state.solution:
                        st.session_state.puzzle_message = "정답입니다! 잘하셨습니다."
                    else:
                        st.session_state.puzzle_message = "아직 정답이 아닙니다. 입력을 다시 확인해 주세요."
            with right:
                if st.button("정답 보기", use_container_width=True):
                    set_board(st.session_state.solution, 9)
                    st.session_state.puzzle_message = "정답을 표시했습니다."
                    st.rerun()

            if st.session_state.get("puzzle_message"):
                st.info(st.session_state.puzzle_message)
                
