
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import time
import math

st.set_page_config(
    page_title="Classic Sudoku",
    page_icon="🔢",
    layout="wide"
)

SYMBOLS = "123456789ABCDEFG"
DIFFICULTIES = ["하", "중", "상", "최상"]
CLUES = {"하": 26, "중": 23, "상": 20, "최상": 17}
MIN_CLUES = {9: 17, 16: 40}

SEED = [
    [0,0,0,0,0,0,0,1,0],
    [4,0,0,0,0,0,0,0,0],
    [0,2,0,0,0,0,0,0,0],
    [0,0,0,0,5,0,4,0,7],
    [0,0,8,0,0,0,3,0,0],
    [0,0,1,0,9,0,0,0,0],
    [3,0,0,4,0,0,2,0,0],
    [0,5,0,1,0,0,0,0,0],
    [0,0,0,8,0,6,0,0,0]
]

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding: 1.2rem 0.6rem;
}

.st-key-sudoku_board {
    max-width: 760px;
    margin-left: auto;
    margin-right: auto;
}

.st-key-sudoku_board [data-testid="stVerticalBlock"] {
    gap: 2px !important;
}

.st-key-sudoku_board [data-testid="stHorizontalBlock"] {
    gap: 2px !important;
}

.st-key-sudoku_board [data-testid="column"] {
    min-width: 0 !important;
    padding: 0 !important;
}

.st-key-sudoku_board button {
    width: 100% !important;
    min-width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    font-weight: 500 !important;
    line-height: 1 !important;
}

.st-key-sudoku_board button p {
    margin: 0 !important;
    padding: 0 !important;
}

.remaining-number {
    text-align: center;
    background: #edf5ff;
    border: 1px solid #b5c7df;
    border-radius: 5px;
    padding: 5px 1px;
    min-height: 58px;
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

.hearts {
    text-align: center;
    font-size: 30px;
    margin: 10px;
}

.timer-background {
    width: 100%;
    height: 18px;
    background: #dedede;
    border-radius: 10px;
    overflow: hidden;
    margin: 8px 0 14px;
}

.timer-progress {
    height: 100%;
    border-radius: 10px;
}

.player-label {
    text-align: center;
    font-size: 25px;
    font-weight: 800;
    margin: 10px 0;
}

.rule-card {
    background: #f0f6ff;
    color: #24364c;
    padding: 18px;
    border-radius: 10px;
    line-height: 1.9;
    border: 1px solid #b8c8dc;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 스도쿠 풀이 엔진
# =====================================================

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


def solve_count(board, n, box, limit=2,
                max_nodes=300000, max_seconds=6):

    count = 0
    solution = None
    nodes = 0
    exhausted = True
    start = time.monotonic()

    def backtrack():
        nonlocal count, solution, nodes, exhausted

        if count >= limit:
            return

        nodes += 1

        if (nodes > max_nodes or
                time.monotonic() - start > max_seconds):
            exhausted = False
            return

        r, c, options = find_empty(board, n, box)

        if r is None:
            count += 1
            if solution is None:
                solution = [row[:] for row in board]
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
    return count, solution, exhausted


def validate(board, n, box):
    for r in range(n):
        values = [v for v in board[r] if v]
        if len(values) != len(set(values)):
            return False, f"{r+1}행에 중복 숫자가 있습니다."

    for c in range(n):
        values = [
            board[r][c] for r in range(n) if board[r][c]
        ]
        if len(values) != len(set(values)):
            return False, f"{c+1}열에 중복 숫자가 있습니다."

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


# =====================================================
# 문제 생성
# =====================================================

def generate_puzzle(target_clues):
    count, original_solution, complete = solve_count(
        [row[:] for row in SEED], 9, 3, limit=2
    )

    if count != 1 or not complete:
        raise RuntimeError("기본 퍼즐 검증에 실패했습니다.")

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
        result = [
            [board[r][c] for c in cols]
            for r in rows
        ]

        if transpose:
            result = [list(row) for row in zip(*result)]

        return [
            [mapping[v] if v else 0 for v in row]
            for row in result
        ]

    puzzle = transform(SEED)
    solution = transform(original_solution)

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


# =====================================================
# 상태 관리
# =====================================================

def initialize_board(board, mode):
    st.session_state.board = [row[:] for row in board]
    st.session_state.selected = None
    st.session_state.board_mode = mode
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


# =====================================================
# 표준 스도쿠 판
# =====================================================

def draw_board(n):
    box = 3 if n == 9 else 4
    selected = st.session_state.selected
    locked = st.session_state.locked

    # 9x9는 넉넉한 셀, 16x16은 작은 셀
    cell_height = 54 if n == 9 else 36
    font_size = 24 if n == 9 else 15

    css = f"""
    <style>
    .st-key-sudoku_board button {{
        height: {cell_height}px !important;
        min-height: {cell_height}px !important;
        font-size: {font_size}px !important;
        background: white !important;
        color: #26384d !important;
        border: 1px solid #b8c5d5 !important;
    }}
    """

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
                background = "#e8dcff"
            elif same_row or same_col or same_box:
                background = "#dceeff"
            elif (r, c) in locked:
                background = "#e9eef5"
            else:
                background = "#ffffff"

            color = "#28548e" if (r, c) in locked else "#26384d"
            weight = "800" if (r, c) in locked else "500"

            border_right = (
                "3px solid #34465c"
                if (c + 1) % box == 0 and c != n - 1
                else "1px solid #b8c5d5"
            )

            border_bottom = (
                "3px solid #34465c"
                if (r + 1) % box == 0 and r != n - 1
                else "1px solid #b8c5d5"
            )

            css += f"""
            .st-key-cell_{r}_{c} button {{
                background: {background} !important;
                color: {color} !important;
                font-weight: {weight} !important;
                border-right: {border_right} !important;
                border-bottom: {border_bottom} !important;
                border-radius: 0 !important;
            }}
            """

    css += "</style>"

    st.markdown(css, unsafe_allow_html=True)

    # 스타일과 버튼을 하나의 컨테이너에 모음
    with st.container(key="sudoku_board"):

        for r in range(n):
            cols = st.columns(n, gap=None)

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


# =====================================================
# 입력
# =====================================================

def apply_entry():
    selected = st.session_state.selected

    if selected is None:
        return

    r, c = selected

    if (r, c) in st.session_state.locked:
        st.session_state.entry_value = ""
        return

    raw = st.session_state.entry_value

    if not raw:
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
        st.session_state.entry_value = ""
        return

    if mode == "puzzle":
        if st.session_state.board[r][c] != 0:
            st.session_state.entry_value = ""
            return

        if value == st.session_state.solution[r][c]:
            st.session_state.board[r][c] = value
        else:
            st.session_state.lives = max(
                0, st.session_state.lives - 1
            )
            if st.session_state.lives == 0:
                st.session_state.game_over = True

        st.session_state.entry_value = ""
        return

    if mode == "versus":
        if st.session_state.phase != "active":
            st.session_state.entry_value = ""
            return

        if time.time() >= st.session_state.deadline:
            st.session_state.winner = 3 - st.session_state.player
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "시간 초과"
            st.session_state.entry_value = ""
            return

        if st.session_state.board[r][c] != 0:
            st.session_state.entry_value = ""
            return

        if value != st.session_state.solution[r][c]:
            st.session_state.winner = 3 - st.session_state.player
            st.session_state.phase = "finished"
            st.session_state.finish_reason = "오답"
            st.session_state.entry_value = ""
            return

        st.session_state.board[r][c] = value

        if all(
            v != 0
            for row in st.session_state.board
            for v in row
        ):
            if st.session_state.level_index == 3:
                st.session_state.winner = st.session_state.player
                st.session_state.phase = "champion"
                st.session_state.entry_value = ""
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
        st.info("스도쿠 판에서 입력할 셀을 선택하십시오.")
        return

    r, c = selected

    if (r, c) in st.session_state.locked:
        st.info("초기 단서는 변경할 수 없습니다.")
        return

    if st.session_state.board[r][c] != 0:
        st.info("이미 숫자가 입력된 셀입니다.")
        return

    st.write(f"선택한 셀: {r+1}행 {c+1}열")

    st.selectbox(
        "입력할 숫자",
        options=[""] + list(SYMBOLS[:n]),
        key="entry_value",
        on_change=apply_entry,
        label_visibility="collapsed",
        format_func=lambda x: x if x else "숫자를 선택하십시오."
    )


# =====================================================
# 남은 숫자
# =====================================================

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
                f'<div class="remaining-number">'
                f'<div class="digit">{SYMBOLS[i-1]}</div>'
                f'<div class="count">{remaining}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# =====================================================
# 1vs1 문제 생성
# =====================================================

def make_versus_level():
    difficulty = DIFFICULTIES[
        st.session_state.level_index
    ]

    puzzle, solution = generate_puzzle(CLUES[difficulty])

    initialize_board(puzzle, "versus")

    st.session_state.solution = solution
    st.session_state.deadline = time.time() + 20
    st.session_state.phase = "active"


# =====================================================
# 세션 초기화
# =====================================================

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
    "finish_reason": "",
    "entry_value": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# 메인 화면
# =====================================================

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


# =====================================================
# 풀이 규격
# =====================================================

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


# =====================================================
# 풀이
# =====================================================

elif st.session_state.page == "solve_board":

    n = st.session_state.solve_n

    st.title(f"{n} × {n} 스도쿠")

    draw_board(n)
    show_entry(n)
    show_remaining(n)

    if st.button("완료", type="primary"):

        board = [row[:] for row in st.session_state.board]
        box = 3 if n == 9 else 4

        clue_count = sum(
            v != 0 for row in board for v in row
        )

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
            count, solution, complete = solve_count(
                [row[:] for row in board],
                n, box, limit=2
            )

            if not complete:
                result = (
                    "불가능",
                    "풀이 검증 시간 초과: 단서를 더 입력해 주십시오."
                )
            elif count == 0:
                result = (
                    "불가능",
                    "규칙 위반: 입력한 단서로 해답을 만들 수 없습니다."
                )
            elif count >= 2:
                result = (
                    "불가능",
                    "단서 부족: 가능한 해답이 여러 개입니다."
                )
            else:
                result = ("가능", solution)

        st.session_state.solve_result = result
        st.rerun()

    result = st.session_state.solve_result

    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.warning(result[1])
        else:
            st.success("풀이 완료")
            st.markdown("### 완성된 스도쿠")

            for row in result[1]:
                st.write(
                    "　".join(SYMBOLS[v-1] for v in row)
                )

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =====================================================
# 문제 선택
# =====================================================

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
        initialize_board(puzzle, "puzzle")

        st.session_state.solution = solution
        st.session_state.lives = 3
        st.session_state.game_over = False
        st.session_state.difficulty = difficulty
        st.session_state.page = "puzzle_play"
        st.rerun()

    st.divider()
    st.subheader("1 vs 1 스도쿠 대전")

    if st.button("1 vs 1 시작", type="primary"):
        st.session_state.level_index = 0
        st.session_state.player = 1
        st.session_state.winner = None
        st.session_state.phase = "rules"
        st.session_state.page = "versus"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =====================================================
# 일반 문제
# =====================================================

elif st.session_state.page == "puzzle_play":

    st.title("스도쿠 문제")

    st.markdown(
        f'<div class="hearts">'
        f'{"❤️ " * st.session_state.lives}'
        f'</div>',
        unsafe_allow_html=True
    )

    if st.session_state.game_over:
        st.error("실패했습니다. 목숨을 모두 사용했습니다.")

    else:
        draw_board(9)
        show_entry(9)
        show_remaining(9)

        if all(
            v != 0
            for row in st.session_state.board
            for v in row
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


# =====================================================
# 1vs1
# =====================================================

elif st.session_state.page == "versus":

    st.title("1 vs 1 스도쿠 대전")

    # 룰 설명
    if st.session_state.phase == "rules":

        st.markdown("""
        <div class="rule-card">
        <h3>대전 규칙</h3>
        1. Player 1부터 시작합니다.<br>
        2. 각 턴에는 20초가 주어집니다.<br>
        3. 제한 시간 안에 한 칸을 정확하게 채우면 상대 차례가 됩니다.<br>
        4. 오답을 입력하거나 시간이 끝나면 패배합니다.<br>
        5. 모든 칸을 채우면 다음 난이도로 올라갑니다.<br>
        6. 난이도는 하 → 중 → 상 → 최상 순서입니다.<br>
        7. 마지막으로 정답을 입력한 플레이어가 다음 난이도를 시작합니다.
        </div>
        """, unsafe_allow_html=True)

        if st.button("대전 시작", type="primary"):

            st.session_state.level_index = 0
            st.session_state.player = 1

            # 카운트다운을 화면에 직접 출력
            countdown_area = st.empty()

            for number in [3, 2, 1]:
                countdown_area.markdown(
                    f"""
                    <div style="text-align:center;padding:25px;">
                        <h2>대전 준비</h2>
                        <div style="font-size:76px;font-weight:800;">
                            {number}
                        </div>
                        <p>Player 1부터 시작합니다.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(1)

            countdown_area.empty()

            make_versus_level()
            st.rerun()

    # 대전 진행
    elif st.session_state.phase == "active":

        st_autorefresh(
            interval=250,
            key=f"active_timer_{st.session_state.level_index}"
        )

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
        color = "#e44b4b" if remaining <= 5 else "#4285d4"

        st.markdown(
            f"""
            <div style="display:flex;justify-content:space-between;">
                <b>남은 시간</b>
                <b>{remaining:.1f}초</b>
            </div>
            <div class="timer-background">
                <div class="timer-progress"
                     style="width:{percentage}%;background:{color};">
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="player-label">'
            f'Player {st.session_state.player} 차례'
            f'</div>',
            unsafe_allow_html=True
        )

        difficulty = DIFFICULTIES[
            st.session_state.level_index
        ]

        st.caption(
            f"현재 난이도: {difficulty} "
            f"({st.session_state.level_index + 1}/4)"
        )

        draw_board(9)
        show_entry(9)
        show_remaining(9)

    # 패배
    elif st.session_state.phase == "finished":

        st.title("대전 종료")
        st.error(
            f"Player {st.session_state.winner} 승리!"
        )

        st.write(
            f"패배 사유: Player "
            f"{3 - st.session_state.winner}의 "
            f"{st.session_state.finish_reason}"
        )

        if st.button("다시 대전하기", type="primary"):
            st.session_state.phase = "rules"
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()

    # 최종 우승
    elif st.session_state.phase == "champion":

        st.title("최종 우승")
        st.balloons()

        st.success(
            f"Player {st.session_state.winner} 최종 우승!"
        )

        st.write(
            "하, 중, 상, 최상 난이도를 모두 완료했습니다."
        )

        if st.button("다시 대전하기", type="primary"):
            st.session_state.phase = "rules"
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()
