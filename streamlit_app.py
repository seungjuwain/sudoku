
import random
import re
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridUpdateMode, DataReturnMode, JsCode

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="centered")

SYMBOLS = "123456789ABCDEFG"
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
    max-width: 720px;
    padding: 1.5rem 0.7rem;
}
h1, h2, h3 { text-align: center; }
div.stButton > button {
    width: 100%;
    min-height: 42px;
    font-size: 16px;
}
div[data-testid="stHorizontalBlock"] {
    gap: 3px !important;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    padding: 0 !important;
    min-width: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 스도쿠 풀이 엔진
# ==================================================
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
        vals = [v for v in board[r] if v]
        if len(vals) != len(set(vals)):
            return False, f"{r + 1}행에 중복 숫자가 있습니다."

    for c in range(n):
        vals = [board[r][c] for r in range(n) if board[r][c]]
        if len(vals) != len(set(vals)):
            return False, f"{c + 1}열에 중복 숫자가 있습니다."

    for br in range(0, n, box):
        for bc in range(0, n, box):
            vals = [
                board[r][c]
                for r in range(br, br + box)
                for c in range(bc, bc + box)
                if board[r][c]
            ]
            if len(vals) != len(set(vals)):
                return False, "같은 구역에 중복 숫자가 있습니다."

    return True, ""


# ==================================================
# 입력값 변환
# ==================================================
def to_dataframe(board):
    n = len(board)
    return pd.DataFrame([
        {
            f"c{c}": SYMBOLS[v - 1] if v else ""
            for c, v in enumerate(row)
        }
        for row in board
    ])


def read_dataframe(data, n):
    board = []

    for r in range(n):
        row = []

        for c in range(n):
            raw = data.iloc[r][f"c{c}"]
            raw = "" if pd.isna(raw) else str(raw).strip().upper()

            if raw == "":
                row.append(0)
            elif len(raw) == 1 and raw in SYMBOLS[:n]:
                row.append(SYMBOLS.index(raw) + 1)
            else:
                raise ValueError(
                    f"{r + 1}행 {c + 1}열: 한 칸에는 "
                    f"{SYMBOLS[:n]} 중 한 글자만 입력할 수 있습니다."
                )

        board.append(row)

    return board


def reset_grid(board):
    st.session_state.grid_version += 1
    st.session_state.grid_data = to_dataframe(board)


# ==================================================
# 스도쿠 판: 정사각형 셀 및 굵은 구역선
# ==================================================
def draw_grid(board, n, box, locked=None, key="grid"):
    locked = locked or set()
    given_coords = [f"{r},{c}" for r, c in locked]

    # JS에서 규격에 맞는 경계선, 선택 행·열·구역 강조를 처리합니다.
    cell_style = JsCode("""
    function(params) {
        const r = params.node.rowIndex;
        const c = Number(params.column.getColId().substring(1));
        const box = params.context.box;
        const focus = params.api.getFocusedCell();
        const style = {
            textAlign: 'center',
            padding: '0',
            fontSize: params.context.n === 9 ? '21px' : '15px',
            borderLeft: c === 0 ? '2px solid #222' : '1px solid #aaa',
            borderTop: r === 0 ? '2px solid #222' : '1px solid #aaa',
            borderRight: (c + 1) % box === 0
                ? '2px solid #222' : '1px solid #aaa',
            borderBottom: (r + 1) % box === 0
                ? '2px solid #222' : '1px solid #aaa'
        };

        if (focus) {
            const fr = focus.rowIndex;
            const fc = Number(focus.column.getColId().substring(1));
            const sameBox =
                Math.floor(r / box) === Math.floor(fr / box) &&
                Math.floor(c / box) === Math.floor(fc / box);

            if (r === fr || c === fc || sameBox) {
                style.backgroundColor = '#dceeff';
            }
        }

        if (params.context.givens.includes(r + ',' + c)) {
            style.fontWeight = 'bold';
            style.color = '#254f91';
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

    # 편집기: 최대 한 글자. 숫자 외 문자와 규격 밖 기호는 거부합니다.
    value_setter = JsCode("""
    function(params) {
        const value = String(params.newValue ?? '').trim().toUpperCase();
        const allowed = params.context.allowed;

        if (value === '') {
            params.data[params.column.getColId()] = '';
            return true;
        }

        if (value.length !== 1 || !allowed.includes(value)) {
            return false;
        }

        params.data[params.column.getColId()] = value;
        return true;
    }
    """)

    on_click = JsCode("""
    function(params) {
        params.api.refreshCells({force: true});
    }
    """)

    column_defs = []
    for c in range(n):
        column_defs.append({
            "field": f"c{c}",
            "headerName": "",
            "width": 48 if n == 9 else 34,
            "minWidth": 24,
            "maxWidth": 50 if n == 9 else 36,
            "editable": editable,
            "valueSetter": value_setter,
            "cellStyle": cell_style,
            "cellEditor": "agTextCellEditor",
            "cellEditorParams": {"maxLength": 1},
            "resizable": False,
            "sortable": False,
            "suppressMovable": True,
        })

    options = {
        "columnDefs": column_defs,
        "rowHeight": 48 if n == 9 else 34,
        "headerHeight": 0,
        "context": {
            "givens": given_coords,
            "box": box,
            "n": n,
            "allowed": SYMBOLS[:n],
        },
        "suppressRowHoverHighlight": True,
        "suppressMovableColumns": True,
        "singleClickEdit": True,
        "stopEditingWhenCellsLoseFocus": True,
        "onCellClicked": on_click,
        "onCellValueChanged": JsCode("""
        function(params) {
            params.api.refreshCells({force: true});
        }
        """),
    }

    result = AgGrid(
        to_dataframe(board),
        gridOptions=options,
        height=n * (48 if n == 9 else 34) + 4,
        width="100%",
        fit_columns_on_grid_load=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        key=key,
        theme="alpine",
    )

    return result


# ==================================================
# 숫자별 남은 개수
# ==================================================
def show_remaining(board, n):
    st.markdown("#### 숫자별 남은 개수")

    counts = {
        v: sum(cell == v for row in board for cell in row)
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
                    padding:6px 0;
                    background:#edf5ff;
                    color:#28548e;
                    font-weight:600;
                ">
                    <div style="font-size:17px">{SYMBOLS[i-1]}</div>
                    <div style="font-size:12px">{remaining}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==================================================
# 문제 생성
# ==================================================
def generate_puzzle(target_clues):
    seed = [
        [int(x) for x in SEED[r * 9:(r + 1) * 9]]
        for r in range(9)
    ]

    count, seed_solution = solve_count(
        [row[:] for row in seed], 9, 3, limit=2
    )

    if count != 1:
        raise RuntimeError("기본 퍼즐의 유일해 검증에 실패했습니다.")

    def shuffled_groups():
        groups = [list(range(3*i, 3*i + 3)) for i in range(3)]
        random.shuffle(groups)
        return [v for g in groups for v in random.sample(g, 3)]

    rows, cols = shuffled_groups(), shuffled_groups()
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

    # 동일한 행·열·숫자 치환을 퍼즐과 해에 적용합니다.
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

    actual = sum(v != 0 for row in puzzle for v in row)
    if actual != target_clues:
        raise RuntimeError("목표 단서 개수 검증에 실패했습니다.")

    return puzzle, solution


# ==================================================
# 상태 초기화
# ==================================================
if "page" not in st.session_state:
    st.session_state.page = "home"

if "grid_version" not in st.session_state:
    st.session_state.grid_version = 0


# ==================================================
# 첫 화면
# ==================================================
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


# ==================================================
# 풀이 규격 선택
# ==================================================
elif st.session_state.page == "solve_select":
    st.title("스도쿠 풀이")

    n = st.radio(
        "규격 선택",
        [9, 16],
        format_func=lambda x: f"{x} × {x}",
        horizontal=True,
    )

    if st.button("빈 판 만들기", type="primary"):
        st.session_state.solve_n = n
        st.session_state.solve_board = [[0] * n for _ in range(n)]
        st.session_state.solve_result = None
        reset_grid(st.session_state.solve_board)
        st.session_state.page = "solve_board"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# ==================================================
# 풀이
# ==================================================
elif st.session_state.page == "solve_board":
    n = st.session_state.solve_n
    box = 3 if n == 9 else 4

    st.title(f"{n} × {n} 스도쿠")
    st.caption("셀을 클릭하여 입력하십시오. 한 칸에는 한 글자만 입력할 수 있습니다.")

    response = draw_grid(
        st.session_state.solve_board,
        n,
        box,
        key=f"solve_{st.session_state.grid_version}",
    )

    show_remaining(st.session_state.solve_board, n)

    if st.button("완료", type="primary"):
        try:
            board = read_dataframe(response["data"], n)
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
                        "입력한 숫자와 스도쿠 규칙을 만족하는 해가 없습니다.",
                    )
                else:
                    st.session_state.solve_result = ("가능", solution)

            st.session_state.solve_board = board
            reset_grid(board)

        except ValueError as error:
            st.session_state.solve_result = ("불가능", str(error))

        st.rerun()

    result = st.session_state.get("solve_result")

    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.write("사유:", result[1])
        else:
            st.success("풀이 완료")
            show_remaining(result[1], n)
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


# ==================================================
# 문제 난이도 선택
# ==================================================
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
            (r, c)
            for r in range(9)
            for c in range(9)
            if puzzle[r][c] != 0
        }

        st.session_state.lives = 3
        st.session_state.game_over = False
        st.session_state.play_feedback = None
        st.session_state.play_board = [row[:] for row in puzzle]
        reset_grid(puzzle)

        st.session_state.page = "puzzle_play"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# ==================================================
# 문제 플레이
# ==================================================
elif st.session_state.page == "puzzle_play":
    puzzle = st.session_state.puzzle
    solution = st.session_state.solution
    locked = st.session_state.puzzle_locked

    st.title(f"스도쿠 — {st.session_state.difficulty}")

    # 목숨은 텍스트 경고 없이 하트로만 표시합니다.
    hearts = "❤️ " * st.session_state.lives
    st.markdown(
        f"<h3 style='text-align:center'>{hearts}</h3>",
        unsafe_allow_html=True,
    )

    if st.session_state.game_over:
        st.error("실패했습니다. 목숨을 모두 사용했습니다.")
    else:
        response = draw_grid(
            st.session_state.play_board,
            9,
            3,
            locked=locked,
            key=f"play_{st.session_state.grid_version}",
        )

        # 서버가 새 입력을 받은 즉시 정답 여부를 검사합니다.
        try:
            current = read_dataframe(response["data"], 9)
            previous = st.session_state.play_board
            wrong_cells = []

            for r in range(9):
                for c in range(9):
                    if (r, c) in locked:
                        continue

                    old = previous[r][c]
                    new = current[r][c]

                    # 새로 입력하거나 다른 값으로 바꾼 셀만 검사합니다.
                    if new != old and new != 0 and new != solution[r][c]:
                        wrong_cells.append((r, c))

            if wrong_cells:
                st.session_state.lives = max(
                    0, st.session_state.lives - len(wrong_cells)
                )

                # 오답은 지워서 다시 입력할 수 있게 합니다.
                for r, c in wrong_cells:
                    current[r][c] = 0

                st.session_state.play_board = current
                reset_grid(current)

                if st.session_state.lives == 0:
                    st.session_state.game_over = True

                # 경고 문구 없이 하트만 갱신합니다.
                st.rerun()

            st.session_state.play_board = current

        except ValueError:
            pass

        show_remaining(st.session_state.play_board, 9)

        if not st.session_state.game_over:
            if st.button("정답 확인", type="primary"):
                board = st.session_state.play_board

                if any(v == 0 for row in board for v in row):
                    st.warning("아직 빈칸이 있습니다.")
                elif board == solution:
                    st.success("정답입니다!")
                else:
                    st.error("아직 정답이 아닙니다.")

    left, right = st.columns(2)

    with left:
        if st.button("새 문제"):
            st.session_state.page = "puzzle_select"
            st.rerun()

    with right:
        if st.button("처음으로"):
            st.session_state.page = "home"
            st.rerun()
