
import random
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="centered")

SYMBOLS = "123456789ABCDEFG"

# 검증용 17단서 기본 퍼즐
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
.block-container {max-width: 760px; padding: 2rem 1rem;}
h1, h2 {text-align: center;}
div.stButton > button {
    width: 100%;
    min-height: 44px;
    font-size: 17px;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 스도쿠 풀이 엔진
# -----------------------------
def candidates(board, r, c, n, box):
    used = set(board[r])
    used.update(board[i][c] for i in range(n))

    br, bc = (r // box) * box, (c // box) * box
    for i in range(br, br + box):
        for j in range(bc, bc + box):
            used.add(board[i][j])

    return set(range(1, n + 1)) - used


def find_empty(board, n, box):
    best = None
    best_opts = None

    for r in range(n):
        for c in range(n):
            if board[r][c] != 0:
                continue

            opts = candidates(board, r, c, n, box)

            if not opts:
                return r, c, set()

            if best is None or len(opts) < len(best_opts):
                best = (r, c)
                best_opts = opts

                if len(opts) == 1:
                    return r, c, opts

    if best is None:
        return None, None, None

    return best[0], best[1], best_opts


def solve_count(board, n, box, limit=2):
    count = 0
    first_solution = None

    def backtrack():
        nonlocal count, first_solution

        if count >= limit:
            return

        r, c, opts = find_empty(board, n, box)

        if r is None:
            count += 1
            if first_solution is None:
                first_solution = [row[:] for row in board]
            return

        if not opts:
            return

        for v in opts:
            board[r][c] = v
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


# -----------------------------
# 문제 생성
# -----------------------------
def generate_solution():
    base, n = 3, 9

    def pattern(r, c):
        return (base * (r % base) + r // base + c) % n

    def shuffled_groups():
        groups = [list(range(3*i, 3*i + 3)) for i in range(3)]
        random.shuffle(groups)
        return [v for g in groups for v in random.sample(g, 3)]

    rows = shuffled_groups()
    cols = shuffled_groups()
    nums = random.sample(range(1, 10), 9)

    return [[nums[pattern(r, c)] for c in cols] for r in rows]


def generate_puzzle(target_clues):
    seed = [
        [int(x) for x in SEED[r * 9:(r + 1) * 9]]
        for r in range(9)
    ]

    count, seed_solution = solve_count([row[:] for row in seed], 9, 3, 2)
    if count != 1:
        raise RuntimeError("기본 퍼즐의 유일해 검증에 실패했습니다.")

    def shuffle_groups():
        groups = [list(range(3*i, 3*i + 3)) for i in range(3)]
        random.shuffle(groups)
        return [v for g in groups for v in random.sample(g, 3)]

    rows, cols = shuffle_groups(), shuffle_groups()
    digits = list(range(1, 10))
    random.shuffle(digits)
    mapping = {i + 1: digits[i] for i in range(9)}
    transpose = random.choice([False, True])

    def transform(board):
        result = [[board[r][c] for c in cols] for r in rows]
        if transpose:
            result = [list(row) for row in zip(*result)]
        return [[mapping[v] if v else 0 for v in row] for row in result]

    puzzle = transform(seed)
    solution = transform(seed_solution)

    # 17단서에서 시작해 지정된 수만큼 단서를 추가합니다.
    empty = [(r, c) for r in range(9) for c in range(9)
             if puzzle[r][c] == 0]
    random.shuffle(empty)

    for r, c in empty[:target_clues - 17]:
        puzzle[r][c] = solution[r][c]

    assert sum(v != 0 for row in puzzle for v in row) == target_clues
    return puzzle, solution


# -----------------------------
# AgGrid 표준 스도쿠 판
# -----------------------------
def grid_data(board):
    return pd.DataFrame([
        {f"c{c}": (SYMBOLS[v - 1] if v else "")
         for c, v in enumerate(row)}
        for row in board
    ])


def read_grid(data, n):
    board = []

    for r in range(n):
        row = []

        for c in range(n):
            raw = data.iloc[r][f"c{c}"]
            raw = "" if pd.isna(raw) else str(raw).strip().upper()

            if not raw:
                row.append(0)
            elif raw in SYMBOLS[:n]:
                row.append(SYMBOLS.index(raw) + 1)
            else:
                raise ValueError(
                    f"{r + 1}행 {c + 1}열에는 "
                    f"{SYMBOLS[:n]} 중 하나를 입력하십시오."
                )

        board.append(row)

    return board


def draw_grid(board, n, box, locked=None, grid_key="sudoku"):
    locked = locked or set()
    given_coords = [f"{r},{c}" for r, c in locked]

    cell_style = JsCode("""
    function(params) {
        const r = params.node.rowIndex;
        const c = Number(params.column.getColId().substring(1));
        const focus = params.api.getFocusedCell();

        let style = {
            textAlign: 'center',
            fontSize: '20px',
            padding: '0',
            borderRadius: '0',
            borderLeft: c === 0 ? '2px solid #333' : '1px solid #aaa',
            borderTop: r === 0 ? '2px solid #333' : '1px solid #aaa',
            borderRight: (c + 1) % 3 === 0
                ? '2px solid #333' : '1px solid #aaa',
            borderBottom: (r + 1) % 3 === 0
                ? '2px solid #333' : '1px solid #aaa'
        };

        if (focus) {
            const fr = focus.rowIndex;
            const fc = Number(focus.column.getColId().substring(1));
            const sameBox =
                Math.floor(r / 3) === Math.floor(fr / 3) &&
                Math.floor(c / 3) === Math.floor(fc / 3);

            if (r === fr || c === fc || sameBox) {
                style.backgroundColor = '#d9f0ff';
            }
        }

        if (params.context.givens.includes(r + ',' + c)) {
            style.fontWeight = 'bold';
        }

        return style;
    }
    """)

    editable = JsCode("""
    function(params) {
        const r = params.node.rowIndex;
        const c = Number(params.column.getColId().substring(1));
        return !params.context.givens.includes(r + ',' + c);
    }
    """)

    on_click = JsCode("""
    function(params) {
        params.api.refreshCells({force: true});
    }
    """)

    on_change = JsCode("""
    function(params) {
        params.api.refreshCells({force: true});
    }
    """)

    column_defs = []
    for c in range(n):
        column_defs.append({
            "field": f"c{c}",
            "headerName": "",
            "width": 48 if n == 9 else 36,
            "minWidth": 28,
            "maxWidth": 52 if n == 9 else 40,
            "editable": editable,
            "cellStyle": cell_style,
            "resizable": False,
            "sortable": False,
            "suppressMovable": True,
        })

    options = {
        "columnDefs": column_defs,
        "rowHeight": 48 if n == 9 else 36,
        "headerHeight": 0,
        "suppressRowHoverHighlight": True,
        "suppressCellFocus": False,
        "suppressMovableColumns": True,
        "singleClickEdit": True,
        "stopEditingWhenCellsLoseFocus": True,
        "context": {"givens": given_coords},
        "onCellClicked": on_click,
        "onCellValueChanged": on_change,
    }

    return AgGrid(
        grid_data(board),
        gridOptions=options,
        height=n * (48 if n == 9 else 36) + 4,
        width="100%",
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        key=grid_key,
        theme="alpine",
    )


# -----------------------------
# 상태 초기화
# -----------------------------
for key, value in {
    "page": "home",
    "solve_result": None,
    "play_feedback": None,
    "lives": 3,
    "game_over": False,
    "board_version": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# 첫 화면
# -----------------------------
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


# -----------------------------
# 풀이 규격 선택
# -----------------------------
elif st.session_state.page == "solve_select":
    st.title("스도쿠 풀이")
    n = st.radio(
        "규격",
        [9, 16],
        format_func=lambda x: f"{x} × {x}",
        horizontal=True,
    )

    if st.button("빈 판 만들기", type="primary"):
        st.session_state.solve_n = n
        st.session_state.solve_board = [[0] * n for _ in range(n)]
        st.session_state.solve_prefix = f"solve_{n}"
        st.session_state.solve_result = None
        st.session_state.board_version += 1
        st.session_state.page = "solve_board"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# -----------------------------
# 풀이 판
# -----------------------------
elif st.session_state.page == "solve_board":
    n = st.session_state.solve_n
    box = 3 if n == 9 else 4

    st.title(f"{n} × {n} 스도쿠")
    st.caption("셀을 클릭하여 입력하고 완료를 누르십시오.")

    response = draw_grid(
        st.session_state.solve_board,
        n,
        box,
        grid_key=f"solve_grid_{st.session_state.board_version}",
    )

    if st.button("완료", type="primary"):
        # 항상 현재 그리드 값을 읽어 새로 판정합니다.
        st.session_state.solve_result = None

        try:
            board = read_grid(response["data"], n)
            valid, reason = validate(board, n, box)

            if not valid:
                st.session_state.solve_result = ("불가능", reason)
            else:
                count, solution = solve_count(
                    [row[:] for row in board], n, box, limit=1
                )

                if count == 0 or solution is None:
                    st.session_state.solve_result = (
                        "불가능",
                        "현재 입력과 스도쿠 규칙을 만족하는 해가 없습니다.",
                    )
                else:
                    st.session_state.solve_result = ("가능", solution)

            st.session_state.solve_board = board

        except ValueError as e:
            st.session_state.solve_result = ("불가능", str(e))

        st.session_state.board_version += 1
        st.rerun()

    result = st.session_state.solve_result
    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.write("사유:", result[1])
        else:
            st.success("풀이 완료")
            st.dataframe(
                pd.DataFrame([
                    [SYMBOLS[v - 1] for v in row]
                    for row in result[1]
                ]),
                hide_index=True,
                use_container_width=True,
            )

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# -----------------------------
# 문제 난이도
# -----------------------------
elif st.session_state.page == "puzzle_select":
    st.title("스도쿠 문제")

    clues = {"하": 26, "중": 23, "상": 20, "최상": 17}
    difficulty = st.radio(
        "난이도",
        ["하", "중", "상", "최상"],
        horizontal=True,
    )
    st.write(f"초기 단서: {clues[difficulty]}개")

    if st.button("문제 생성", type="primary"):
        puzzle, solution = generate_puzzle(clues[difficulty])

        st.session_state.puzzle = puzzle
        st.session_state.solution = solution
        st.session_state.difficulty = difficulty
        st.session_state.puzzle_locked = {
            (r, c) for r in range(9) for c in range(9)
            if puzzle[r][c] != 0
        }
        st.session_state.lives = 3
        st.session_state.game_over = False
        st.session_state.play_feedback = None
        st.session_state.last_play_board = [row[:] for row in puzzle]
        st.session_state.board_version += 1
        st.session_state.page = "puzzle_play"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# -----------------------------
# 문제 플레이
# -----------------------------
elif st.session_state.page == "puzzle_play":
    puzzle = st.session_state.puzzle
    solution = st.session_state.solution
    locked = st.session_state.puzzle_locked

    st.title(f"스도쿠 — {st.session_state.difficulty}")
    st.subheader(f"남은 목숨: {st.session_state.lives} ❤️")

    if st.session_state.game_over:
        st.error("실패했습니다. 목숨을 모두 사용했습니다.")
    else:
        response = draw_grid(
            st.session_state.last_play_board,
            9,
            3,
            locked=locked,
            grid_key=f"play_grid_{st.session_state.board_version}",
        )

        # 셀 입력 변경을 감지하여 새로 입력된 오답만 목숨에서 차감합니다.
        if response is not None and response.get("data") is not None:
            try:
                current = read_grid(response["data"], 9)
                previous = st.session_state.last_play_board

                wrong_entries = []
                for r in range(9):
                    for c in range(9):
                        if (r, c) in locked:
                            continue

                        old = previous[r][c]
                        new = current[r][c]

                        if new != old and new != 0 and new != solution[r][c]:
                            wrong_entries.append((r, c))

                if wrong_entries:
                    st.session_state.lives = max(
                        0, st.session_state.lives - len(wrong_entries)
                    )

                    if st.session_state.lives == 0:
                        st.session_state.game_over = True
                        st.session_state.play_feedback = (
                            "error", "목숨을 모두 사용했습니다."
                        )
                    else:
                        st.session_state.play_feedback = (
                            "error",
                            f"오답입니다. 목숨이 {len(wrong_entries)}개 차감되었습니다."
                        )

                st.session_state.last_play_board = current

            except ValueError:
                pass

        feedback = st.session_state.play_feedback
        if feedback:
            if feedback[0] == "error":
                st.error(feedback[1])
            elif feedback[0] == "success":
                st.success(feedback[1])

        if not st.session_state.game_over:
            if st.button("정답 확인", type="primary"):
                board = st.session_state.last_play_board

                if any(v == 0 for row in board for v in row):
                    st.warning("아직 빈칸이 있습니다.")
                elif board == solution:
                    st.session_state.play_feedback = (
                        "success", "정답입니다!"
                    )
                    st.rerun()
                else:
                    st.session_state.play_feedback = (
                        "error", "아직 정답이 아닙니다."
                    )
                    st.rerun()

    left, right = st.columns(2)
    with left:
        if st.button("새 문제"):
            st.session_state.page = "puzzle_select"
            st.rerun()
    with right:
        if st.button("처음으로"):
            st.session_state.page = "home"
            st.rerun()
