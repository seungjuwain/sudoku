import streamlit as st
import random
import math

st.set_page_config(page_title="스도쿠", page_icon="🔢", layout="centered")

st.title("🔢 스도쿠")
st.write("스도쿠를 직접 풀거나 새로운 문제에 도전하세요.")

SYMBOLS = "123456789ABCDEFG"


def valid(board, n, r, c, v):
    b = int(math.sqrt(n))
    for k in range(n):
        if k != c and board[r][k] == v:
            return False
        if k != r and board[k][c] == v:
            return False

    br, bc = (r // b) * b, (c // b) * b
    for rr in range(br, br + b):
        for cc in range(bc, bc + b):
            if (rr != r or cc != c) and board[rr][cc] == v:
                return False
    return True


def solve(board, n, limit=2):
    b = int(math.sqrt(n))
    solutions = []

    def dfs():
        if len(solutions) >= limit:
            return

        best = None
        candidates = None

        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    used = set(board[r])
                    used.update(board[i][c] for i in range(n))
                    for rr in range((r // b) * b, (r // b) * b + b):
                        for cc in range((c // b) * b, (c // b) * b + b):
                            used.add(board[rr][cc])

                    opts = [v for v in range(1, n + 1) if v not in used]
                    if not opts:
                        return
                    if candidates is None or len(opts) < len(candidates):
                        best = (r, c)
                        candidates = opts
                        if len(opts) == 1:
                            break
            if candidates is not None and len(candidates) == 1:
                break

        if best is None:
            solutions.append([row[:] for row in board])
            return

        r, c = best
        for v in candidates:
            board[r][c] = v
            dfs()
            board[r][c] = 0
            if len(solutions) >= limit:
                return

    dfs()
    return solutions


def empty_board(n):
    return [[0] * n for _ in range(n)]


def generate_puzzle(difficulty):
    # 표준 스도쿠 완성판을 만든 뒤 단서를 제거합니다.
    base = [
        [((r * 3 + r // 3 + c) % 9) + 1 for c in range(9)]
        for r in range(9)
    ]

    digits = list(range(1, 10))
    random.shuffle(digits)
    board = [[digits[v - 1] for v in row] for row in base]

    bands = list(range(3))
    random.shuffle(bands)
    rows = []
    for band in bands:
        within = list(range(3))
        random.shuffle(within)
        rows.extend([band * 3 + x for x in within])
    board = [board[r] for r in rows]

    stacks = list(range(3))
    random.shuffle(stacks)
    cols = []
    for stack in stacks:
        within = list(range(3))
        random.shuffle(within)
        cols.extend([stack * 3 + x for x in within])
    board = [[row[c] for c in cols] for row in board]

    answer = [row[:] for row in board]
    clues = {"최상": 17, "상": 20, "중": 23, "하": 26}[difficulty]

    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)
    for r, c in positions[:81 - clues]:
        board[r][c] = 0

    return board, answer


if "mode" not in st.session_state:
    st.session_state.mode = "메뉴"
if "board" not in st.session_state:
    st.session_state.board = empty_board(9)
if "givens" not in st.session_state:
    st.session_state.givens = set()
if "answer" not in st.session_state:
    st.session_state.answer = None
if "message" not in st.session_state:
    st.session_state.message = ""
if "revision" not in st.session_state:
    st.session_state.revision = 0

if st.session_state.mode == "메뉴":
    st.subheader("메뉴")
    c1, c2 = st.columns(2)

    if c1.button("풀이", use_container_width=True):
        st.session_state.mode = "풀이 설정"
        st.rerun()

    if c2.button("문제", use_container_width=True):
        st.session_state.mode = "문제 설정"
        st.rerun()

elif st.session_state.mode == "풀이 설정":
    st.subheader("풀이할 스도쿠 규격")
    size = st.radio("규격", [9, 16], format_func=lambda x: f"{x} × {x}")

    if st.button("시작", type="primary"):
        st.session_state.board = empty_board(size)
        st.session_state.givens = set()
        st.session_state.answer = None
        st.session_state.message = ""
        st.session_state.revision += 1
        st.session_state.mode = "게임"
        st.session_state.game_mode = "풀이"
        st.session_state.rerun_key = 0
        st.rerun()

    if st.button("메뉴로 돌아가기"):
        st.session_state.mode = "메뉴"
        st.rerun()

elif st.session_state.mode == "문제 설정":
    st.subheader("난이도 선택")
    difficulty = st.radio("난이도", ["하", "중", "상", "최상"])

    if st.button("문제 생성", type="primary"):
        puzzle, answer = generate_puzzle(difficulty)
        st.session_state.board = puzzle
        st.session_state.givens = {
            (r, c) for r in range(9) for c in range(9) if puzzle[r][c]
        }
        st.session_state.answer = answer
        st.session_state.message = ""
        st.session_state.difficulty = difficulty
        st.session_state.revision += 1
        st.session_state.mode = "게임"
        st.session_state.game_mode = "문제"
        st.rerun()

    if st.button("메뉴로 돌아가기"):
        st.session_state.mode = "메뉴"
        st.rerun()

elif st.session_state.mode == "게임":
    board = st.session_state.board
    n = len(board)
    b = int(math.sqrt(n))
    st.subheader(
        f"{'풀이' if st.session_state.game_mode == '풀이' else '문제'} · {n}×{n}"
    )

    st.caption("각 행, 열, 구역에는 같은 숫자가 중복될 수 없습니다.")

    # 데이터 편집용 표
    data = []
    for r in range(n):
        row = {}
        for c in range(n):
            row[f"C{c+1}"] = SYMBOLS[board[r][c]-1] if board[r][c] else ""
        data.append(row)

    edited = st.data_editor(
        data,
        key=f"editor_{st.session_state.revision}",
        hide_index=True,
        use_container_width=True,
        disabled=False,
        column_config={
            f"C{c+1}": st.column_config.TextColumn(
                f"{c+1}", max_chars=1, width="small"
            ) for c in range(n)
        },
    )

    # 편집값을 숫자로 변환
    current = empty_board(n)
    invalid_input = False

    for r in range(n):
        for c in range(n):
            raw = str(edited[r][f"C{c+1}"]).strip().upper()
            if not raw:
                current[r][c] = 0
            elif raw in SYMBOLS[:n]:
                current[r][c] = SYMBOLS.index(raw) + 1
            else:
                invalid_input = True

    st.session_state.board = current

    if st.session_state.message:
        st.info(st.session_state.message)

    if st.session_state.game_mode == "풀이":
        if st.button("완료", type="primary"):
            if invalid_input:
                st.session_state.message = "풀이 불가능: 허용되지 않는 기호가 있습니다."
            else:
                bad = None
                for r in range(n):
                    for c in range(n):
                        if current[r][c] and not valid(current, n, r, c, current[r][c]):
                            bad = f"{r+1}행 {c+1}열의 숫자가 규칙을 위반합니다."
                            break
                    if bad:
                        break

                if bad:
                    st.session_state.message = "풀이 불가능: " + bad
                else:
                    solutions = solve(current, n, 2)
                    if not solutions:
                        st.session_state.message = (
                            "풀이 불가능: 현재 단서를 만족하는 해답이 없습니다."
                        )
                    elif len(solutions) > 1:
                        st.session_state.message = (
                            "풀이 불가능: 해답이 여러 개입니다. 단서를 더 입력해 주세요."
                        )
                    else:
                        st.session_state.board = solutions[0]
                        st.session_state.message = "풀이 완료!"
                        st.session_state.revision += 1
            st.rerun()

    else:
        c1, c2 = st.columns(2)
        if c1.button("정답 확인", use_container_width=True):
            if invalid_input:
                st.session_state.message = "허용되지 않는 기호가 있습니다."
            elif current == st.session_state.answer:
                st.session_state.message = "정답입니다! 스도쿠를 완성했습니다."
            else:
                st.session_state.message = "아직 정답이 아닙니다."
            st.rerun()

        if c2.button("힌트", use_container_width=True):
            ans = st.session_state.answer
            found = False
            for r in range(n):
                for c in range(n):
                    if current[r][c] == 0:
                        current[r][c] = ans[r][c]
                        st.session_state.board = current
                        st.session_state.givens.add((r, c))
                        found = True
                        break
                if found:
                    break
            st.session_state.message = "빈칸에 힌트를 채웠습니다." if found else "빈칸이 없습니다."
            st.session_state.revision += 1
            st.rerun()

    if st.button("메뉴로 돌아가기"):
        st.session_state.mode = "메뉴"
        st.rerun()
