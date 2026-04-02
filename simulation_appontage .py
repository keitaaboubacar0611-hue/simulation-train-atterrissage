"""
================================================================
  Simulation Amortisseur Train d'Atterrissage — Appontage
  Rafale-M | Safran Landing Systems
================================================================
  Auteur  : Keita Aboubacar — ENIB Brest
  Contexte: Projet académique inspiré du dimensionnement réel
            de l'amortisseur avant du Rafale-M (2025)

  Physique :
    Système masse-ressort-amortisseur linéaire du 2nd ordre.
    Équation du mouvement :
        m·x''(t) + c·x'(t) + k·x(t) = m·g

    L'amortisseur absorbe l'énergie cinétique de l'impact
    et doit respecter les critères Safran Landing Systems :
        - Décélération pilote < 3g
        - Course amortisseur < course disponible
        - Stabilisation en < 2 secondes

  Étude paramétrique :
    Comparaison de 3 configurations d'amortissement pour
    identifier le réglage optimal de l'orifice de laminage.
================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp


# ══════════════════════════════════════════════════════════════
# 1. PARAMÈTRES COMMUNS
# ══════════════════════════════════════════════════════════════

m            = 9500.0    # Masse aéronef [kg]
g            = 9.81      # Gravité [m/s²]
k            = 300000.0  # Raideur ressort pneumatique [N/m]
v_impact     = 6.5       # Vitesse verticale d'appontage [m/s]
course_max   = 0.40      # Course maximale amortisseur [m]

# Équilibre statique
x_static     = m * g / k
course_dispo = course_max - x_static

print("=" * 58)
print("  PARAMÈTRES DU SYSTÈME")
print("=" * 58)
print(f"  Masse aéronef         : {m:.0f} kg")
print(f"  Raideur               : {k/1000:.0f} kN/m")
print(f"  Vitesse d'impact      : {v_impact} m/s")
print(f"  Compression statique  : {x_static*100:.1f} cm")
print(f"  Course disponible     : {course_dispo*100:.1f} cm")
print("=" * 58)


# ══════════════════════════════════════════════════════════════
# 2. CONFIGURATIONS D'AMORTISSEMENT
# ══════════════════════════════════════════════════════════════

configs = [
    {"label": "Sous-amorti  (c = 50 kN·s/m)",  "c": 50_000,  "color": "tomato"},
    {"label": "Optimal      (c = 180 kN·s/m)", "c": 180_000, "color": "royalblue"},
    {"label": "Sur-amorti   (c = 600 kN·s/m)", "c": 600_000, "color": "seagreen"},
]


# ══════════════════════════════════════════════════════════════
# 3. RÉSOLUTION NUMÉRIQUE (RK45)
# ══════════════════════════════════════════════════════════════

t_end  = 4.0
t_eval = np.linspace(0, t_end, 8000)
results = []

for cfg in configs:
    c = cfg["c"]

    def systeme(t, y, c=c):
        x, v = y
        xc = max(0.0, min(x, course_max * 0.99))
        a  = (m * g - k * xc - c * v) / m
        return [v, a]

    sol = solve_ivp(
        systeme, [0, t_end], [x_static, v_impact],
        t_eval=t_eval, method='RK45', max_step=2e-4, rtol=1e-9
    )

    t  = sol.t
    x  = sol.y[0]
    v  = sol.y[1]
    dx = x - x_static
    a_g = np.array([
        (m*g - k*max(0.0, min(xi, course_max*0.99)) - c*vi) / m / g
        for xi, vi in zip(x, v)
    ])
    results.append({**cfg, "t": t, "x": x, "dx": dx, "v": v, "a_g": a_g})


# ══════════════════════════════════════════════════════════════
# 4. BILAN — CRITÈRES DE VALIDATION SAFRAN
# ══════════════════════════════════════════════════════════════

print("\n  BILAN PAR CONFIGURATION")
print("=" * 58)
print(f"  {'Configuration':28} | {'Décel.':>7} | {'Course':>7} | Stab.")
print("-" * 58)

for r in results:
    peak   = np.max(np.abs(r["a_g"][20:]))
    stroke = np.max(r["dx"]) * 100
    idx    = np.where((r["t"] > 0.2) & (np.abs(r["v"]) < 0.1))[0]
    stab   = f"{r['t'][idx[0]]:.2f} s" if len(idx) > 0 else "> 4 s"
    ok     = "OK" if peak < 3.0 and stroke < course_dispo * 100 else "hors spec"
    print(f"  {r['label'][:28]:28} | {peak:5.1f} g  | {stroke:5.1f} cm | {stab} [{ok}]")

print("=" * 58)
print(f"  Course disponible : {course_dispo*100:.1f} cm  |  Limite : 3.0 g")


# ══════════════════════════════════════════════════════════════
# 5. GRAPHIQUES
# ══════════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle(
    "Simulation Amortisseur Train d'Atterrissage — Appontage Rafale-M\n"
    f"v_impact = {v_impact} m/s  |  m = {m:.0f} kg  |  k = {k/1000:.0f} kN/m\n"
    "Étude paramétrique : influence du coefficient d'amortissement c",
    fontsize=11, fontweight='bold'
)

ax1 = axes[0, 0]
for r in results:
    ax1.plot(r["t"], r["dx"]*100, label=r["label"], color=r["color"], lw=2)
ax1.axhline(course_dispo*100, color='red', lw=1.5, ls='--',
            label=f'Course dispo. ({course_dispo*100:.0f} cm)')
ax1.axhline(0, color='gray', lw=0.8, ls=':')
ax1.set_title("Compression supplémentaire Δx(t)")
ax1.set_xlabel("Temps [s]"); ax1.set_ylabel("Compression [cm]")
ax1.legend(fontsize=8); ax1.grid(True, alpha=0.3); ax1.set_xlim([0, t_end])

ax2 = axes[0, 1]
for r in results:
    ax2.plot(r["t"], r["v"], label=r["label"], color=r["color"], lw=2)
ax2.axhline(0, color='gray', lw=0.8, ls=':')
ax2.axhline(0.1, color='orange', lw=1.2, ls='--', label='Seuil stab. (0.1 m/s)')
ax2.set_title("Vitesse de compression v(t)")
ax2.set_xlabel("Temps [s]"); ax2.set_ylabel("Vitesse [m/s]")
ax2.legend(fontsize=8); ax2.grid(True, alpha=0.3)
ax2.set_xlim([0, t_end]); ax2.set_ylim([-3, 8])

ax3 = axes[1, 0]
for r in results:
    ax3.plot(r["t"], np.abs(r["a_g"]), label=r["label"], color=r["color"], lw=2)
ax3.axhline(3.0, color='darkred', lw=2, ls='--', label='Limite tolérance humaine (3g)')
ax3.fill_between(results[0]["t"], 3, 10, alpha=0.07, color='red', label='Zone hors spec')
ax3.set_title("Décélération subie par le pilote |a(t)|")
ax3.set_xlabel("Temps [s]"); ax3.set_ylabel("Décélération [g]")
ax3.legend(fontsize=8); ax3.grid(True, alpha=0.3)
ax3.set_xlim([0, 1.5]); ax3.set_ylim([0, 10])

ax4 = axes[1, 1]
for r in results:
    ax4.plot(r["dx"]*100, r["v"], label=r["label"], color=r["color"], lw=2)
    ax4.scatter([r["dx"][0]*100], [r["v"][0]], color=r["color"], s=60, zorder=5)
ax4.axhline(0, color='gray', lw=0.8, ls=':')
ax4.axvline(0, color='gray', lw=0.8, ls=':')
ax4.scatter([0], [0], color='black', s=120, marker='*', zorder=6, label='Équilibre')
ax4.set_title("Portrait de phase (Δx, v)")
ax4.set_xlabel("Compression supplémentaire [cm]"); ax4.set_ylabel("Vitesse [m/s]")
ax4.legend(fontsize=8); ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("resultats_appontage.png", dpi=150, bbox_inches="tight")
plt.show()
print("\n  Graphiques sauvegardés → resultats_appontage.png")
