import streamlit as st
import numpy as np
import random

# --- BB84 simulation logic ---
def simulate_bb84(shots=512, p_eve=0.0, channel_error=0.0):
    alice_bits = np.random.randint(2, size=shots)
    alice_bases = np.random.randint(2, size=shots)  # 0=Z, 1=X
    bob_bases   = np.random.randint(2, size=shots)

    bob_bits = np.copy(alice_bits)

    # Eve’s interception
    if p_eve > 0:
        eve_bases = np.random.randint(2, size=shots)
        eve_bits  = np.copy(alice_bits)
        flip = eve_bases != alice_bases
        eve_bits[flip] = np.random.randint(2, size=np.sum(flip))
        # resend
        resend_bits = eve_bits
        resend_bases = eve_bases
        bob_bits = np.copy(resend_bits)
        wrong_basis = bob_bases != resend_bases
        bob_bits[wrong_basis] = np.random.randint(2, size=np.sum(wrong_basis))

    # Channel noise
    noise = np.random.rand(shots) < channel_error
    bob_bits[noise] ^= 1

    # Sifted key
    sift = alice_bases == bob_bases
    alice_sift = alice_bits[sift]
    bob_sift   = bob_bits[sift]

    return alice_sift, bob_sift

def estimate_qber(alice_sift, bob_sift, fraction=0.25):
    if len(alice_sift) == 0:
        return None
    n = max(1, int(len(alice_sift) * fraction))
    idx = random.sample(range(len(alice_sift)), n)
    errors = sum(alice_sift[i] != bob_sift[i] for i in idx)
    return errors / n

# --- Streamlit UI ---
st.title("🔑 BB84 Quantum Key Distribution Simulator")

shots = st.slider("Number of qubits (shots)", 50, 2000, 512, step=50)
eve_choice = st.radio("Eve’s interception level", ["None", "50%", "100%"])
channel_error = st.slider("Channel noise (0–100%)", 0.0, 1.0, 0.0, step=0.05)

# Convert Eve choice to probability
p_eve = {"None": 0.0, "50%": 0.5, "100%": 1.0}[eve_choice]

if st.button("Run Simulation"):
    alice_sift, bob_sift = simulate_bb84(shots, p_eve, channel_error)
    qber = estimate_qber(alice_sift, bob_sift)

    st.write(f"📏 **Sifted key length:** {len(alice_sift)}")
    if qber is None:
        st.error("Not enough sifted bits to estimate QBER.")
    else:
        st.write(f"❌ **Estimated QBER:** {qber:.2%}")
        if qber > 0.11:
            st.error("🚨 ABORT: Eve likely detected (QBER too high).")
        else:
            st.success("✅ Key is secure!")
            st.code("".join(map(str, alice_sift[:32])) + "...")
