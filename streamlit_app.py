import random
import streamlit as st

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="centered")

# ---------- Sudoku engine ----------
def candidates(board, r, c, n, box):
    used = set(board[r])
    used.update(board[i][c] for i in range(n))
    br, bc = (r // box) * box, (c // box) * box
    for i in range(br, br + box):
        for j in range(bc, bc + box):
            used.add(board[i][j])
    return set(range(1, n + 1)) - used

def find_empty_mrv(board, n, box):
    best = None
    best_cands = None
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                opts = candidates(board, r, c, n, box)
                if not opts:
                    return r, c, set()
                if best is None or len(opts) < len(best_cands):
                    best, best_cands = (r, c), opts
                    if len(opts) == 1:
                        return r, c, opts
    return (best[0], best[1], best_cands) if best else (None, None, None)

def solve_count(board, n, box, limit=2, randomize=False):
    """Count solutions up to limit; restore board after search."""
    count = 0
    first_solution = None

    def backtrack():
        nonlocal count, first_solution
        if count >= limit:
            return
        r, c, opts = find_empty_mrv(board, n, box)
        if r is None:
            count += 1
            if first_solution is None:
                first_solution = [row[:] for row in board]
            return
        if not opts:
            return
        vals = list(opts)
        if randomize:
            random.shuffle(vals)
        for v in vals:
            board[r][c] = v
            backtrack()
            board[r][c] = 0
            if count >= limit:
                return

    backtrack()
    return count, first_solution

def solve_one(board, n, box):
    count, solution = solve_count(board, n, box, limit=1)
    return solution

def valid_partial(board, n, box):
    for r in range(n):
        vals = [x for x in board[r] if x]
        if len(vals) != len(set(vals)):
            return False, f"{r+1}행에 같은 숫자가 중복되어 있습니다."
    for c in range(n):
        vals = [board[r][c] for r in range(n) if board[r][c]]
        if len(vals) != len(set(vals)):
            return False, f"{c+1}열에 같은 숫자가 중복되어 있습니다."
    for br in range(0, n, box):
        for bc in range(0, n, box):
            vals = [board[r][c] for r in range(br, br+box)
                    for c in range(bc, bc+box) if board[r][c]]
            if len(vals) != len(set(vals)):
                return False, f"{br+1}~{br+box}행, {bc+1}~{bc+box}열 구역에 중복 숫자가 있습니다."
    return True, ""

def shuffled_solution_9():
    # Pattern-based complete 9x9 solution with randomized bands, stacks, rows, columns and symbols.
    base, side = 3, 9
    def pattern(r, c): return (base * (r % base) + r // base + c) % side
    def shuffle_groups():
        groups = [list(range(base*i, base*(i+1))) for i in range(base)]
        random.shuffle(groups)
        return [x for group in groups for x in random.sample(group, len(group))]
    rows, cols = shuffle_groups(), shuffle_groups()
    nums = random.sample(range(1, 10), 9)
    return [[nums[pattern(r, c)] for c in cols] for r in rows]

def make_puzzle(clues):
    solution = shuffled_solution_9()
    puzzle = [row[:] for row in solution]
    cells = list(range(81))
    random.shuffle(cells)
    removed = 0
    for idx in cells:
        if 81 - removed <= clues:
            break
        r, c = divmod(idx, 9)
        old = puzzle[r][c]
        puzzle[r][c] = 0
        count, _ = solve_count([row[:] for row in puzzle], 9, 3, limit=2)
        if count != 1:
            puzzle[r][c] = old
        else:
            removed += 1
    return puzzle, solution

def board_from_state(prefix, n):
    board = []
    for r in range(n):
        row = []
        for c in range(n):
            value = st.session_state.get(f"{prefix}_{r}_{c}", 0)
            row.append(int(value) if value else 0)
        board.append(row)
    return board

def reset_grid(prefix, n, values=None, locked=None):
    values = values or [[0]*n for _ in range(n)]
    locked = locked or set()
    for r in range(n):
        for c in range(n):
            key = f"{prefix}_{r}_{c}"
            st.session_state[key] = str(values[r][c]) if values[r][c] else ""
            if (r, c) in locked:
                st.session_state[f"{prefix}_lock_{r}_{c}"] = True
            else:
                st.session_state[f"{prefix}_lock_{r}_{c}"] = False

def draw_grid(prefix, n, box, disabled_cells=None):
    disabled_cells = disabled_cells or set()
    for r in range(n):
        cols = st.columns(n, gap="small")
        for c in range(n):
            key = f"{prefix}_{r}_{c}"
            value = st.session_state.get(key, 0)
            options = [""] + [str(i) for i in range(1, n+1)]
            current = str(value) if value else ""
            with cols[c]:
                # Streamlit cannot style each cell's borders reliably, so use a clean standard grid.
                st.selectbox(
                    f"r{r+1}c{c+1}", options,
                    index=options.index(current),
                    key=key,
                    label_visibility="collapsed",
                    disabled=(r, c) in disabled_cells,
                )

# ---------- Session state ----------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "solve_n" not in st.session_state:
    st.session_state.solve_n = 9
if "puzzle_board" not in st.session_state:
    st.session_state.puzzle_board = None
if "puzzle_solution" not in st.session_state:
    st.session_state.puzzle_solution = None
if "puzzle_locked" not in st.session_state:
    st.session_state.puzzle_locked = set()

st.markdown("""
<style>
.block-container {max-width: 1000px; padding-top: 2rem; padding-bottom: 3rem;}
h1, h2, h3 {text-align:center;}
div.stButton > button {width:100%; min-height:3rem; font-size:1.05rem;}
div[data-testid="stSelectbox"] label {font-size:0.7rem;}
</style>
""", unsafe_allow_html=True)

if st.session_state.page == "home":
    st.title("🔢 스도쿠")
    st.write("")
    left, right = st.columns(2)
    with left:
        if st.button("풀이", use_container_width=True):
            st.session_state.page = "solve_select"
            st.rerun()
    with right:
        if st.button("문제", use_container_width=True):
            st.session_state.page = "puzzle_select"
            st.rerun()

elif st.session_state.page == "solve_select":
    st.title("스도쿠 풀이")
    n = st.radio("스도쿠 규격 선택", [9, 16], format_func=lambda x: f"{x} × {x}", horizontal=True)
    if st.button("빈 판 만들기"):
        st.session_state.solve_n = n
        st.session_state.solve_prefix = f"solve_{n}"
        reset_grid(st.session_state.solve_prefix, n)
        st.session_state.solve_result = None
        st.session_state.page = "solve_board"
        st.rerun()
    if st.button("뒤로"):
        st.session_state.page = "home"
        st.rerun()

elif st.session_state.page == "solve_board":
    n = st.session_state.solve_n
    box = 3 if n == 9 else 4
    prefix = st.session_state.solve_prefix
    st.title(f"{n} × {n} 스도쿠 풀이")
    st.caption(f"각 칸에서 숫자를 선택하세요. 16×16은 1~16을 사용합니다.")
    draw_grid(prefix, n, box)
    if st.button("완료", type="primary"):
        board = board_from_state(prefix, n)
        ok, reason = valid_partial(board, n, box)
        if not ok:
            st.session_state.solve_result = ("불가능", reason)
        else:
            count, solution = solve_count([row[:] for row in board], n, box, limit=1)
            if solution is None:
                st.session_state.solve_result = ("불가능", "현재 입력한 숫자와 스도쿠 규칙을 동시에 만족하는 해가 없습니다.")
            else:
                st.session_state.solve_result = ("가능", solution)
        st.rerun()
    result = st.session_state.get("solve_result")
    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.write(f"사유: {result[1]}")
        else:
            st.success("풀이 완료")
            st.write("완성된 스도쿠")
            solution = result[1]
            for row in solution:
                st.write("　".join(str(x) for x in row))
    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()

elif st.session_state.page == "puzzle_select":
    st.title("스도쿠 문제")
    difficulty = st.radio("난이도 선택", ["하", "중", "상", "최상"], horizontal=True)
    clue_map = {"최상": 17, "상": 20, "중": 23, "하": 26}
    st.caption(f"단서 {clue_map[difficulty]}개 · 유일한 해가 있는 문제")
    if st.button("문제 생성", type="primary"):
        with st.spinner("문제를 생성하고 있습니다..."):
            puzzle, solution = make_puzzle(clue_map[difficulty])
        st.session_state.puzzle_board = puzzle
        st.session_state.puzzle_solution = solution
        st.session_state.puzzle_locked = {(r,c) for r in range(9) for c in range(9) if puzzle[r][c]}
        st.session_state.puzzle_difficulty = difficulty
        st.session_state.page = "puzzle_play"
        reset_grid("play", 9, puzzle)
        st.rerun()
    if st.button("뒤로"):
        st.session_state.page = "home"
        st.rerun()

elif st.session_state.page == "puzzle_play":
    st.title(f"스도쿠 — {st.session_state.puzzle_difficulty}")
    st.caption("빈칸을 채운 뒤 정답 확인을 누르세요.")
    locked = st.session_state.puzzle_locked
    draw_grid("play", 9, 3, disabled_cells=locked)
    left, right = st.columns(2)
    with left:
        if st.button("정답 확인", type="primary"):
            board = board_from_state("play", 9)
            ok, reason = valid_partial(board, 9, 3)
            if not ok:
                st.session_state.play_feedback = ("error", reason)
            elif any(board[r][c] == 0 for r in range(9) for c in range(9)):
                st.session_state.play_feedback = ("warning", "아직 빈칸이 있습니다.")
            elif board == st.session_state.puzzle_solution:
                st.session_state.play_feedback = ("success", "정답입니다! 잘 풀었습니다.")
            else:
                st.session_state.play_feedback = ("error", "아직 정답이 아닙니다. 숫자를 다시 확인해 보세요.")
            st.rerun()
    with right:
        if st.button("새 문제"):
            st.session_state.page = "puzzle_select"
            st.rerun()
    feedback = st.session_state.get("play_feedback")
    if feedback:
        {"error": st.error, "warning": st.warning, "success": st.success}[feedback[0]](feedback[1])
    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()
