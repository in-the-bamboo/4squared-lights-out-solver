import streamlit as st
import numpy as np
from z3 import Optimize, Int, Sum, sat

# --- Z3 求解ロジック (先ほどと同じもの) ---
def solve_lights_out_4x4_z3(initial_state):
    A1 = np.zeros((16, 16), dtype=int)
    A2 = np.zeros((16, 16), dtype=int)
    for i in range(16):
        r1, c1 = divmod(i, 4)
        for j in range(16):
            r2, c2 = divmod(j, 4)
            if abs(r1 - r2) + abs(c1 - c2) <= 1:
                A1[j, i] = 1
            if max(abs(r1 - r2), abs(c1 - c2)) <= 1:
                A2[j, i] = 1

    opt = Optimize()
    X = [Int(f'x_{i}') for i in range(16)]
    Y = [Int(f'y_{i}') for i in range(16)]

    for i in range(16):
        opt.add(X[i] >= 0, X[i] <= 1)
        opt.add(Y[i] >= 0, Y[i] <= 1)

    for j in range(16):
        influence = 0
        for i in range(16):
            if A1[j, i] == 1: influence += X[i]
            if A2[j, i] == 1: influence += Y[i]
        opt.add(influence % 2 == initial_state[j])

    total_steps = Sum(X + Y)
    opt.minimize(total_steps)

    if opt.check() == sat:
        model = opt.model()
        ans_X = [model[X[i]].as_long() for i in range(16)]
        ans_Y = [model[Y[i]].as_long() for i in range(16)]
        return ans_X, ans_Y, sum(ans_X) + sum(ans_Y)
    else:
        return None, None, None

# --- Streamlit UI構築 ---
st.set_page_config(page_title="Lights Out 最短ソルバー", layout="centered")
st.title("💡 Lights Out 最短手数ソルバー (4x4)")
st.markdown("操作1(十字)と操作2(斜め込)を組み合わせて、指定した盤面を最短でクリアする手順をZ3ソルバーが計算します。")

# 1. 盤面の状態管理 (Session State)
# Streamlitはボタンを押すたびに画面が再描画されるため、状態を保持する仕組みを使います
if 'board' not in st.session_state:
    st.session_state.board = [0] * 16 # 0:表, 1:裏

# 全てリセットするボタン
if st.button("盤面をリセット"):
    st.session_state.board = [0] * 16
    st.rerun()

st.write("### ⬇️ 初期状態をセットしてください")
st.write("ボタンをクリックすると表(⬛)と裏(🟨)が切り替わります。")

# 2. 4x4の入力用グリッドUI
# st.columnsを使ってボタンを横に並べます
for row in range(4):
    cols = st.columns(4)
    for col in range(4):
        idx = row * 4 + col
        # 現在の状態に応じてアイコンを変更
        label = "🟨 裏" if st.session_state.board[idx] == 1 else "⬛ 表"
        
        # ボタンが押されたら、そのマスの状態を反転して再描画
        if cols[col].button(label, key=f"btn_{idx}"):
            st.session_state.board[idx] = 1 - st.session_state.board[idx]
            st.rerun()

st.divider()

# 3. 求解ボタンと結果表示
if st.button("🚀 最短手数を計算する", type="primary"):
    with st.spinner("Z3ソルバーが43億通りから最短ルートを探索中..."):
        ans_X, ans_Y, min_steps = solve_lights_out_4x4_z3(st.session_state.board)
    
    if ans_X is not None:
        st.success(f"🎉 クリア可能です！ 最短手数: **{min_steps}手**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### ➕ 操作1 (十字)")
            # 1(押す)の場所を🔴、0を⬜にして表示
            for r in range(4):
                row_str = ""
                for c in range(4):
                    if ans_X[r*4 + c] == 1:
                        row_str += "🔴"
                    else:
                        row_str += "⬜"
                st.write(row_str)
                
        with col2:
            st.write("#### ✖️ 操作2 (斜め込)")
            # 1(押す)の場所を🔵、0を⬜にして表示
            for r in range(4):
                row_str = ""
                for c in range(4):
                    if ans_Y[r*4 + c] == 1:
                        row_str += "🔵"
                    else:
                        row_str += "⬜"
                st.write(row_str)
    else:
        st.error("この状態からはクリア不可能です。（パズルの法則上、到達できない盤面です）")
