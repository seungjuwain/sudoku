import random
import streamlit as st

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="wide")

SYMBOLS = "123456789ABCDEFG"

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
    
    # 격자 컨테이너 크기 계산 (9x9 기준 약 450px~500px 정사각형)
    cell_size = 50 if n == 9 else 32
    board_width = cell_size * n + 6

    # CSS 렌더링
    st.markdown(f"""
    <style>
    .sudoku-container {{
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }}
    .sudoku-board-{n} {{
        display: grid;
        grid-template-columns: repeat({n}, {cell_size}px);
        grid-template-rows: repeat({n}, {cell_size}px);
        width: {board_width}px;
        border: 3px solid #000000;
        background-color: #000000;
        gap: 0px;
    }}
    .sudoku-cell-wrap {{
        width: {cell_size}px;
        height: {cell_size}px;
        box-sizing: border-box;
        background: white;
    }}
    /* 입력창 스타일 */
    .stTextInput input {{
        height: {cell_size}px !important;
        width: {cell_size}px !important;
        text-align: center !important;
        font-size: {22 if n == 9 else 15}px !important;
        font-weight: bold !important;
        border-radius: 0px !important;
        border: none !important;
        padding: 0 !important;
    }}
    /* 박스 구역 구분 (검은색 실선) */
    .border-top {{ border-top: 3px solid #000000 !important; }}
    .border-left {{ border-left: 3px solid #000000 !important; }}
    .border-inner {{ border: 1px solid #d0d0d0; }}
    </style>
    """, unsafe_allow_html=True)

    # 3x3 / 4x4 구역 분할 구조 생성
    for r in range(n):
        cols = st.columns(n)
        for c in range(n):
            key = f"cell_{n}_{r}_{c}"
            
            # 셀별 테두리 조건
            top_class = "border-top" if (r % box == 0 and r != 0) else ""
            left_class = "border-left" if (c % box == 0 and c != 0) else ""
            
            with cols[c]:
                st.markdown(f'<div class="{top_class} {left_class} border-inner">', unsafe_allow_html=True)
                st.text_input(
                    f"{r+1}-{c+1}",
                    key=key,
                    max_chars=1,
                    label_visibility="collapsed",
                    disabled=(r, c) in fixed
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
        
        # 중앙 정렬을 위한 컬럼 분할
        c1, c2, c3 = st.columns([1, 8, 1])
        with c2:
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
            
            c1, c2, c3 = st.columns([1, 8, 1])
            with c2:
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
