import streamlit as st
import numpy as np
import random
import pandas as pd

# --- BB84 simulation logic ---
def simulate_bb84(shots=20, p_eve=0.0, channel_error=0.0):
    alice_bits = np.random.randint(2, size=shots)
    alice_bases = np.random.choice(["Z", "X"], size=shots)
    bob_bases   = np.random.choice(["Z", "X"], size=shots)

    # Bob’s measurement initially same as Alice
    bob_bits = np.copy(alice_bits)

    eve_bases = np.array(["-"] * shots)
    eve_bits  = np.array(["-"] * shots)

    # Eve’s interception
    if p_eve > 0:
        eve_bases = np.random.choice(["Z", "X"], size=shots)
        eve_bits  = np.copy(alice_bits).astype(str)

        # If Eve uses wrong basis → random outcome
        wrong_eve = eve_bases != alice_bases
        eve_bits[wrong_eve] = np.random.randint(2, size=np.sum(wrong_eve)).astype(str)

        # Resend
        resend_bits = eve_bits.astype(int)
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

    # Return all details for visualization
    return alice_bits, alice_bases, eve_bits, eve_bases, bob_bits, bob_bases, sift, alice_sift, bob_sift


def estimate_qber(alice_sift, bob_sift, fraction=0.25):
    if len(alice_sift) == 0:
        return None
    n = max(1, int(len(alice_sift) * fraction))
    idx = random.sample(range(len(alice_sift)), n)
    errors = sum(alice_sift[i] != bob_sift[i] for i in idx)
    return errors / n


# --- Streamlit UI ---
st.title("🔑 BB84 Quantum Key Distribution Simulator")

shots = st.slider("Number of qubits (shots)", 10, 100, 20, step=5)
eve_choice = st.radio("Eve’s interception level", ["None", "50%", "100%"])
channel_error = st.slider("Channel noise (0–100%)", 0.0, 1.0, 0.0, step=0.05)

p_eve = {"None": 0.0, "50%": 0.5, "100%": 1.0}[eve_choice]

if st.button("Run Simulation"):
    alice_bits, alice_bases, eve_bits, eve_bases, bob_bits, bob_bases, sift, alice_sift, bob_sift = simulate_bb84(
        shots, p_eve, channel_error
    )
    qber = estimate_qber(alice_sift, bob_sift)

    # --- Show transfer table ---
    df = pd.DataFrame({
        "Alice Bit": alice_bits,
        "Alice Basis": alice_bases,
        "Eve Basis": eve_bases,
        "Eve Bit": eve_bits,
        "Bob Basis": bob_bases,
        "Bob Bit": bob_bits,
        "Bases Match?": ["✅" if alice_bases[i] == bob_bases[i] else "❌" for i in range(shots)],
        "Sifted?": ["✅" if sift[i] else "❌" for i in range(shots)]
    })

    st.subheader("🔎 Transmission Details")
    st.dataframe(df)

    # --- Results ---
    st.subheader("📊 Results")
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
