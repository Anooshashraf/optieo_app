import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from .. import theme
from ..model import compute_all, efficiency


class ChartsWidget(QWidget):
    """Parameter trade-off curves + a live efficiency breakdown, all recomputed
    from the *current* input state so they always match the control deck."""

    def __init__(self, parent=None):
        super().__init__(parent)
        plt.style.use('dark_background')
        self.figure, (self.ax1, self.ax2, self.ax3) = plt.subplots(1, 3, figsize=(15, 4.6))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.figure.patch.set_facecolor(theme.PANEL_2)
        for ax in (self.ax1, self.ax2, self.ax3):
            ax.set_facecolor(theme.PANEL_2)
        self._ax1_twin = None
        self._ax2_twin = None

    def update_charts(self, P):
        alt_vals = [300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200]
        ap_vals = [0.2, 0.5, 0.8, 1.1, 1.4, 1.7, 2.0, 2.3, 2.6, 3.0]

        # remove any previously-created twin axes so they don't stack up
        if self._ax1_twin is not None:
            self._ax1_twin.remove()
        if self._ax2_twin is not None:
            self._ax2_twin.remove()

        # ---- Altitude trade-off ----
        alt_data = []
        for a in alt_vals:
            p = dict(P)
            p['altitude'] = a
            o = compute_all(p)
            alt_data.append((o['GSD'], o['finalSNR']))

        self.ax1.clear()
        self.ax1.set_title("Altitude vs GSD & SNR", color=theme.TEXT, fontsize=11, fontweight='bold')
        self.ax1.set_xlabel("Altitude (km)", color=theme.TEXT_DIM, fontsize=9)
        l1 = self.ax1.plot(alt_vals, [d[0] for d in alt_data], color=theme.CYAN, marker='o', ms=3, label="GSD (m)")
        self.ax1.set_ylabel("GSD (m)", color=theme.CYAN, fontsize=9)
        self.ax1.tick_params(axis='x', colors=theme.TEXT_DIM, labelsize=8)
        self.ax1.tick_params(axis='y', colors=theme.CYAN, labelsize=8)
        self.ax1.axvline(P['altitude'], color=theme.TEXT_FAINT, ls='--', lw=1)
        self._ax1_twin = self.ax1.twinx()
        self._ax1_twin.set_facecolor('none')
        l2 = self._ax1_twin.plot(alt_vals, [d[1] for d in alt_data], color=theme.CORAL, marker='o', ms=3, label="SNR")
        self._ax1_twin.set_ylabel("Final SNR", color=theme.CORAL, fontsize=9)
        self._ax1_twin.tick_params(axis='y', colors=theme.CORAL, labelsize=8)
        self.ax1.legend([l1[0], l2[0]], ["GSD (m)", "SNR"], loc="upper left", fontsize=8, framealpha=0.15)

        # ---- Aperture trade-off ----
        ap_data = []
        for ap in ap_vals:
            p = dict(P)
            p['aperture'] = ap
            o = compute_all(p)
            ap_data.append((o['GSD'], o['finalSNR']))

        self.ax2.clear()
        self.ax2.set_title("Aperture vs GSD & SNR", color=theme.TEXT, fontsize=11, fontweight='bold')
        self.ax2.set_xlabel("Aperture (m)", color=theme.TEXT_DIM, fontsize=9)
        l3 = self.ax2.plot(ap_vals, [d[0] for d in ap_data], color=theme.CYAN, marker='o', ms=3, label="GSD (m)")
        self.ax2.set_ylabel("GSD (m)", color=theme.CYAN, fontsize=9)
        self.ax2.tick_params(axis='x', colors=theme.TEXT_DIM, labelsize=8)
        self.ax2.tick_params(axis='y', colors=theme.CYAN, labelsize=8)
        self.ax2.axvline(P['aperture'], color=theme.TEXT_FAINT, ls='--', lw=1)
        self._ax2_twin = self.ax2.twinx()
        self._ax2_twin.set_facecolor('none')
        l4 = self._ax2_twin.plot(ap_vals, [d[1] for d in ap_data], color=theme.CORAL, marker='o', ms=3, label="SNR")
        self._ax2_twin.set_ylabel("Final SNR", color=theme.CORAL, fontsize=9)
        self._ax2_twin.tick_params(axis='y', colors=theme.CORAL, labelsize=8)
        self.ax2.legend([l3[0], l4[0]], ["GSD (m)", "SNR"], loc="upper left", fontsize=8, framealpha=0.15)

        # ---- Live efficiency breakdown ----
        O = compute_all(P)
        eff = efficiency(O)
        labels = ["Spatial", "Radiometric", "Temporal", "Dynamic"]
        vals = [eff['spatial'], eff['radiometric'], eff['temporal'], eff['dynamic']]
        colors = [theme.SPATIAL, theme.RADIOMETRIC, theme.ORBITAL, theme.VIOLET]
        self.ax3.clear()
        self.ax3.set_title(f"Efficiency Breakdown  (overall {eff['overall']:.0f})", color=theme.TEXT,
                            fontsize=11, fontweight='bold')
        bars = self.ax3.bar(labels, vals, color=colors, width=0.55)
        for b, v in zip(bars, vals):
            self.ax3.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.0f}", ha='center',
                           color=theme.TEXT, fontsize=8, fontweight='bold')
        self.ax3.set_ylim(0, 110)
        self.ax3.tick_params(axis='x', colors=theme.TEXT_DIM, labelsize=8)
        self.ax3.tick_params(axis='y', colors=theme.TEXT_DIM, labelsize=8)
        self.ax3.spines['top'].set_visible(False)
        self.ax3.spines['right'].set_visible(False)

        for ax in (self.ax1, self.ax2, self.ax3):
            for spine in ax.spines.values():
                spine.set_color(theme.LINE)

        self.figure.tight_layout(pad=1.6)
        self.canvas.draw_idle()
