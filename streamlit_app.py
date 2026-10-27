import random
import streamlit as st
import streamlit.components.v1 as components

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

def render_sudoku_board(n, box, fixed=None):
    fixed = fixed or set()
    cell_size = 50 if n == 9 else 34
    
    # 순수 HTML/CSS 구현
    html_code = f"""
    <style>
        .sudoku-table {{
            border-collapse: collapse;
            margin: 0 auto;
            border: 3px solid #000000;
            background-color: #ffffff;
        }}
        .sudoku-table td {{
            width: {cell_size}px;
            height: {cell_size}px;
            padding: 0;
            margin: 0;
            border: 1px solid #c0c0c0; /* 회색 실선 */
            text-align: center;
        }}
        /* 3x3 / 4x4 구역 검은색 굵은 실선 */
        .border-top {{ border-top: 3px solid #000000 !important; }}
        .border-left {{ border-left: 3px solid #000000 !important; }}
        
        .sudoku-input {{
            width: 100%;
            height: 100%;
            border: none;
            text-align: center;
            font-size: {22 if n == 9 else 16}px;
            font-weight: bold;
            color: #111111;
            background: transparent;
            outline: none;
            box-sizing: border-box;
            text-transform: uppercase;
        }}
        .sudoku-input:focus {{
            background-color: #e8f4fe;
        }}
        .sudoku-input:disabled {{
            background-color: #f0f2f5;
            color: #000000;
            font-weight: 800;
        }}
    </style>
    
    <table class="sudoku-table">
    """
    
    for r in range(n):
        html_code += "<tr>"
        for c in range(n):
            top_class = "border-top" if (r % box == 0 and r != 0) else ""
            left_class = "border-left" if (c % box == 0 and c != 0) else ""
            is_disabled = "disabled" if (r, c) in fixed else ""
            
            val = st.session_state.get(f"cell_{n}_{r}_{c}", "")
            
            html_code += f"""
            <td class="{top_class} {left_class}">
                <input type="text" 
                       class="sudoku-input" 
                       maxlength="1" 
                       value="{val}" 
                       {is_disabled}
                       oninput="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: 'cell_{n}_{r}_{c}', value: this.value.toUpperCase()}}, '*')"
                       id="input_{r}_{c}">
            </td>
            """
        html_code += "</tr>"
    html_code += "</table>"
    
    # 폼 입력을 Streamlit st.text_input 컴포넌트 방식으로 깔끔하게 대체
    for r in range(n):
        cols = st.columns(n, gap=None)
        for c in range(n):
            key = f"cell_{n}_{r}_{c}"
            if key not in st.session_state:
                st.session_state[key] = ""

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

# CSS 레벨에서 레이아웃 강제 교정
st.markdown("""
<style>
div[data-testid="column"] {
    padding: 0 !important;
    min-width: 0 !important;
}
div[data-testid="stHorizontalBlock"] {
    gap: 0px !important;
}
div[data-testid="stTextInput"] input {
    aspect-ratio: 1 / 1 !important;
    height: auto !important;
    min-height: 0 !important;
    text-align: center !important;
    font-size: 20px !important;
    font-weight: bold !important;
    border-radius: 0 !important;
    border: 1px solid #c0c0c0 !important;
    padding: 0 !important;
}
div[data-testid="stTextInput"] label { display: none !important; }

/* 굵은 경계선 설정 */
.b-top { border-top: 3px solid #000000 !important; }
.b-bottom { border-bottom: 3px solid #000000 !important; }
.b-left { border-left: 3px solid #000000 !important; }
.b-right { border-right: 3px solid #000000 !important; }
</style>
""", unsafe_allow_html=True)

def draw_clean_board(n, box, fixed=None):
    fixed = fixed or set()
    for r in range(n):
        cols = st.columns(n, gap=None)
        for c in range(n):
            key = f"cell_{n}_{r}_{c}"
            classes = []
            if r % box == 0: classes.append("b-top")
            if r == n - 1: classes.append("b-bottom")
            if c % box == 0: classes.append("b-left")
            if c == n - 1: classes.append("b-right")
            
            cls_str = " ".join(classes)
            with cols[c]:
                if cls_str:
                    st.markdown(f'<div class="{cls_str}">', unsafe_allow_html=True)
                st.text_input(
                    f"{r}-{c}",
                    key=key,
                    max_chars=1,
                    disabled=(r, c) in fixed
                )
                if cls_str:
                    st.markdown('</div>', unsafe_allow_html=True)

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
        
        # 보드 출력
        draw_clean_board(n, box)

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
            
            draw_clean_board(9, 3, st.session_state.puzzle_fixed)

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
