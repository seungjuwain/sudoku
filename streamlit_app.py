
import streamlit as st
import random
import time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Classic Sudoku", page_icon="🔢", layout="wide")

SYMBOLS = "123456789ABCDEFG"
LEVELS = ["하", "중", "상", "최상"]
CLUES = {"하": 26, "중": 23, "상": 20, "최상": 17}

# ==================================================
# CSS: 표준 스도쿠 격자
# ==================================================

st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding: 1rem 0.5rem;
}

/* 스도쿠 판 전체 */
.st-key-sudoku_board {
    width: 100% !important;
    max-width: 650px !important;
    margin: 0 auto !important;
}

/* 행 사이의 불필요한 여백 제거 */
.st-key-sudoku_board [data-testid="stVerticalBlock"] {
    gap: 0px !important;
    row-gap: 0px !important;
}

/* 행 */
.st-key-sudoku_board [data-testid="stHorizontalBlock"] {
    gap: 0px !important;
    column-gap: 0px !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* 셀 열 */
.st-key-sudoku_board [data-testid="column"] {
    min-width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* 셀 버튼 */
.st-key-sudoku_board button {
    width: 100% !important;
    min-width: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    aspect-ratio: 1 / 1 !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    line-height: 1 !important;
    font-size: clamp(11px, 2.5vw, 25px) !important;
}

/* 버튼 내부 */
.st-key-sudoku_board button p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
}

/* 숫자별 남은 개수 */
.remaining-number {
    text-align: center;
    background: #edf5ff;
    border: 1px solid #b5c7df;
    border-radius: 5px;
    padding: 5px 1px;
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
</style>
""", unsafe_allow_html=True)


# ==================================================
# 스도쿠 엔진
# ==================================================

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
    count = 0
    solution = None
    nodes = 0
    start = time.time()

    def backtrack():
        nonlocal count, solution, nodes

        if count >= limit or nodes > 300000:
            return

        nodes += 1

        if time.time() - start > 5:
            return

        r, c, options = find_empty(board, n, box)

        if r is None:
            count += 1
            if solution is None:
                solution = [row[:] for row in board]
            return

        if not options:
            return

        for v in options:
            board[r][c] = v
            backtrack()
            board[r][c] = 0

            if count >= limit:
                return

    backtrack()
    return count, solution


def validate(board, n, box):
    for r in range(n):
        vals = [v for v in board[r] if v]
        if len(vals) != len(set(vals)):
            return False, f"{r+1}행에 중복 숫자가 있습니다."

    for c in range(n):
        vals = [board[r][c] for r in range(n) if board[r][c]]
        if len(vals) != len(set(vals)):
            return False, f"{c+1}열에 중복 숫자가 있습니다."

    for br in range(0, n, box):
        for bc in range(0, n, box):
            vals = [
                board[r][c]
                for r in range(br, br+box)
                for c in range(bc, bc+box)
                if board[r][c]
            ]
            if len(vals) != len(set(vals)):
                return False, "같은 구역에 중복 숫자가 있습니다."

    return True, ""


def generate_solution(n):
    box = int(n ** 0.5)
    nums = list(range(1, n + 1))
    random.shuffle(nums)

    bands = list(range(box))
    random.shuffle(bands)

    rows = []
    for band in bands:
        inside = list(range(box))
        random.shuffle(inside)
        rows.extend([band * box + x for x in inside])

    stacks = list(range(box))
    random.shuffle(stacks)

    cols = []
    for stack in stacks:
        inside = list(range(box))
        random.shuffle(inside)
        cols.extend([stack * box + x for x in inside])

    return [
        [
            nums[(box * (r % box) + r // box + c) % n]
            for c in cols
        ]
        for r in rows
    ]


def generate_puzzle(clue_count):
    solution = generate_solution(9)
    puzzle = [row[:] for row in solution]

    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)

    for r, c in cells:
        if sum(v != 0 for row in puzzle for v in row) <= clue_count:
            break

        old = puzzle[r][c]
        puzzle[r][c] = 0

        count, _ = solve_count(
            [row[:] for row in puzzle], 9, 3, 2
        )

        if count != 1:
            puzzle[r][c] = old

    return puzzle, solution


# ==================================================
# 세션 초기화
# ==================================================

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
    "entry_value": "",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def initialize_board(board, mode):
    st.session_state.board = [row[:] for row in board]
    st.session_state.board_mode = mode
    st.session_state.selected = None
    st.session_state.entry_value = ""

    n = len(board)
    st.session_state.locked = {
        (r, c)
        for r in range(n)
        for c in range(n)
        if board[r][c] != 0
    }


def select_cell(r, c):
    st.session_state.selected = (r, c)
    st.session_state.entry_value = ""


# ==================================================
# 스도쿠 판 출력
# ==================================================

def draw_board(n):
    box = int(n ** 0.5)
    selected = st.session_state.selected
    locked = st.session_state.locked

    # 셀의 배경 및 구역 경계 CSS
    css = "<style>"

    for r in range(n):
        for c in range(n):
            is_selected = selected == (r, c)

            same_row = selected is not None and selected[0] == r
            same_col = selected is not None and selected[1] == c
            same_box = (
                selected is not None
                and selected[0] // box == r // box
                and selected[1] // box == c // box
            )

            if is_selected:
                bg = "#e8dcff"
            elif same_row or same_col:
                bg = "#dceeff"
            elif same_box:
                bg = "#dceeff"
            elif (r, c) in locked:
                bg = "#e9eef5"
            else:
                bg = "#ffffff"

            color = "#28548e" if (r, c) in locked else "#26384d"

            right = (
                "3px solid #202b38"
                if (c + 1) % box == 0 and c != n - 1
                else "1px solid #aeb8c4"
            )

            bottom = (
                "3px solid #202b38"
                if (r + 1) % box == 0 and r != n - 1
                else "1px solid #aeb8c4"
            )

            css += f"""
            .st-key-cell_{r}_{c} button {{
                background-color: {bg} !important;
                color: {color} !important;
                border-right: {right} !important;
                border-bottom: {bottom} !important;
            }}
            """

    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)

    # 중요: 컨테이너 자체의 gap을 0으로 설정
    with st.container(key="sudoku_board", gap="0px"):

        for r in range(n):
            cols = st.columns(n, gap="small")

            for c in range(n):
                value = st.session_state.board[r][c]
                label = SYMBOLS[value - 1] if value else " "

                with cols[c]:
                    st.button(
                        label,
                        key=f"cell_{r}_{c}",
                        use_container_width=True,
                        on_click=select_cell,
                        args=(r, c)
                    )


# ==================================================
# 숫자 입력
# ==================================================

def apply_entry():
    selected = st.session_state.selected
    if selected is None:
        return

    r, c = selected

    if (r, c) in st.session_state.locked:
        st.session_state.entry_value = ""
        return

    raw = st.session_state.entry_value

    if raw not in SYMBOLS:
        return

    n = len(st.session_state.board)

    if raw not in SYMBOLS[:n]:
        st.session_state.entry_value = ""
        return

    value = SYMBOLS.index(raw) + 1
    mode = st.session_state.board_mode

    if mode == "solve":
        st.session_state.board[r][c] = value
        st.session_state.solve_result = None

    elif mode == "puzzle":
        if st.session_state.board[r][c] != 0:
            return

        if value == st.session_state.solution[r][c]:
            st.session_state.board[r][c] = value
        else:
            st.session_state.lives -= 1
            if st.session_state.lives <= 0:
                st.session_state.lives = 0
                st.session_state.game_over = True

    elif mode == "versus":
        if st.session_state.phase != "active":
            return

        if time.time() >= st.session_state.deadline:
            st.session_state.winner = 3 - st.session_state.player
            st.session_state.phase = "finished"
            return

        if st.session_state.board[r][c] != 0:
            return

        if value != st.session_state.solution[r][c]:
            st.session_state.winner = 3 - st.session_state.player
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "오답"
            return

        st.session_state.board[r][c] = value

        if all(v != 0 for row in st.session_state.board for v in row):
            if st.session_state.level_index == 3:
                st.session_state.winner = st.session_state.player
                st.session_state.phase = "champion"
                return

            st.session_state.level_index += 1
            make_versus_level()
            return

        st.session_state.player = 3 - st.session_state.player
        st.session_state.deadline = time.time() + 20

    st.session_state.entry_value = ""


def show_entry(n):
    selected = st.session_state.selected

    if selected is None:
        st.info("입력할 셀을 선택하십시오.")
        return

    r, c = selected

    if (r, c) in st.session_state.locked:
        st.info("초기 단서는 변경할 수 없습니다.")
        return

    if st.session_state.board[r][c] != 0:
        st.info("이미 숫자가 입력된 셀입니다.")
        return

    st.selectbox(
        "숫자 입력",
        [""] + list(SYMBOLS[:n]),
        key="entry_value",
        on_change=apply_entry,
        format_func=lambda x: x if x else "숫자 선택",
        label_visibility="collapsed"
    )


# ==================================================
# 남은 숫자
# ==================================================

def show_remaining(n):
    st.markdown("#### 숫자별 남은 개수")

    cols = st.columns(n, gap="small")

    for i, col in enumerate(cols, 1):
        used = sum(
            cell == i
            for row in st.session_state.board
            for cell in row
        )

        with col:
            st.markdown(
                f"""
                <div class="remaining-number">
                    <div class="digit">{SYMBOLS[i-1]}</div>
                    <div class="count">{n-used}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ==================================================
# 1vs1 다음 단계 생성
# ==================================================

def make_versus_level():
    difficulty = LEVELS[st.session_state.level_index]
    puzzle, solution = generate_puzzle(CLUES[difficulty])

    initialize_board(puzzle, "versus")
    st.session_state.solution = solution
    st.session_state.deadline = time.time() + 20
    st.session_state.phase = "active"


# ==================================================
# 메인
# ==================================================

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


# ==================================================
# 풀이 규격 선택
# ==================================================

elif st.session_state.page == "solve_select":

    st.title("스도쿠 풀이")

    n = st.radio(
        "규격 선택",
        [9, 16],
        horizontal=True,
        format_func=lambda x: f"{x} × {x}"
    )

    if st.button("빈 판 만들기", type="primary"):
        initialize_board([[0]*n for _ in range(n)], "solve")
        st.session_state.solve_n = n
        st.session_state.solve_result = None
        st.session_state.page = "solve_board"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# ==================================================
# 풀이 화면
# ==================================================

elif st.session_state.page == "solve_board":

    n = st.session_state.solve_n

    st.title(f"{n} × {n} 스도쿠")

    draw_board(n)
    show_entry(n)
    show_remaining(n)

    if st.button("완료", type="primary"):

        board = [row[:] for row in st.session_state.board]
        box = int(n ** 0.5)

        clue_count = sum(v != 0 for row in board for v in row)
        valid, reason = validate(board, n, box)

        if not valid:
            result = ("불가능", f"규칙 위반: {reason}")

        elif clue_count < MIN_CLUES[n]:
            result = (
                "불가능",
                f"단서 부족: 현재 {clue_count}개입니다. "
                f"최소 {MIN_CLUES[n]}개가 필요합니다."
            )

        else:
            count, solution = solve_count(board, n, box, 2)

            if count == 0:
                result = ("불가능", "입력한 단서로 해답을 만들 수 없습니다.")
            elif count >= 2:
                result = ("불가능", "단서 부족: 가능한 해답이 여러 개입니다.")
            elif solution:
                result = ("가능", solution)
            else:
                result = ("불가능", "풀이 검증에 실패했습니다.")

        st.session_state.solve_result = result
        st.rerun()

    if st.session_state.solve_result:
        result = st.session_state.solve_result

        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.warning(result[1])
        else:
            st.success("풀이 완료")
            for row in result[1]:
                st.write("　".join(SYMBOLS[v-1] for v in row))

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# ==================================================
# 문제 선택
# ==================================================

elif st.session_state.page == "puzzle_select":

    st.title("스도쿠 문제")

    difficulty = st.radio(
        "난이도",
        LEVELS,
        horizontal=True
    )

    st.write(f"초기 단서: {CLUES[difficulty]}개")

    if st.button("문제 생성", type="primary"):
        puzzle, solution = generate_puzzle(CLUES[difficulty])

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
        st.session_state.phase = "rules"
        st.session_state.winner = None
        st.session_state.page = "versus"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# ==================================================
# 일반 문제
# ==================================================

elif st.session_state.page == "puzzle_play":

    st.title("스도쿠 문제")

    st.markdown(
        f'<div style="font-size:28px;text-align:center;">'
        f'{"❤️ " * st.session_state.lives}</div>',
        unsafe_allow_html=True
    )

    if st.session_state.game_over:
        st.error("실패했습니다. 목숨을 모두 사용했습니다.")

    else:
        draw_board(9)
        show_entry(9)
        show_remaining(9)

        if all(v != 0 for row in st.session_state.board for v in row):
            st.success("정답입니다!")

    if st.button("새 문제"):
        st.session_state.page = "puzzle_select"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# ==================================================
# 1vs1 대전
# ==================================================

elif st.session_state.page == "versus":

    st.title("1 vs 1 스도쿠 대전")

    if st.session_state.phase == "rules":

        st.markdown("""
        ### 대전 규칙

        - Player 1부터 시작합니다.
        - 한 턴에 20초가 주어집니다.
        - 20초 안에 정확히 한 칸을 채우면 상대 턴으로 넘어갑니다.
        - 오답 또는 시간 초과 시 패배합니다.
        - 한 난이도를 전부 풀면 다음 난이도로 올라갑니다.
        - 난이도는 하 → 중 → 상 → 최상 순서입니다.
        """)

        if st.button("대전 시작", type="primary"):
            st.session_state.phase = "countdown"
            st.session_state.countdown_end = time.time() + 3
            st.rerun()

    elif st.session_state.phase == "countdown":

        st_autorefresh(interval=200, key="countdown_refresh")

        remaining = max(
            0,
            int(st.session_state.countdown_end - time.time()) + 1
        )

        if time.time() >= st.session_state.countdown_end:
            make_versus_level()
            st.rerun()

        st.markdown(
            f"""
            <div style="text-align:center;padding:50px;">
                <h2>대전 준비</h2>
                <div style="font-size:80px;font-weight:800;">
                    {remaining}
                </div>
                Player 1부터 시작합니다.
            </div>
            """,
            unsafe_allow_html=True
        )

    elif st.session_state.phase == "active":

        st_autorefresh(interval=250, key="versus_refresh")

        remaining = max(
            0,
            st.session_state.deadline - time.time()
        )

        if remaining <= 0:
            st.session_state.winner = 3 - st.session_state.player
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "시간 초과"
            st.rerun()

        percentage = remaining / 20 * 100

        st.markdown(
            f"""
            **남은 시간: {remaining:.1f}초**
            <div style="height:18px;background:#ddd;border-radius:10px;">
                <div style="
                    height:18px;
                    width:{percentage}%;
                    background:#4285d4;
                    border-radius:10px;">
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.subheader(f"Player {st.session_state.player} 차례")

        st.caption(
            f"난이도: {LEVELS[st.session_state.level_index]}"
        )

        draw_board(9)
        show_entry(9)
        show_remaining(9)

    elif st.session_state.phase == "finished":

        st.error(f"Player {st.session_state.winner} 승리!")
        st.write(
            f"패배 사유: {st.session_state.finish_reason}"
        )

        if st.button("다시 대전"):
            st.session_state.phase = "rules"
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()

    elif st.session_state.phase == "champion":

        st.balloons()
        st.success(
            f"Player {st.session_state.winner} 최종 우승!"
        )

        if st.button("다시 대전"):
            st.session_state.phase = "rules"
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()
