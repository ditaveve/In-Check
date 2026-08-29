from itertools import zip_longest

from ..storage import db


class PlayerComparison:
    def __init__(self, username_a, username_b):
        self.username_a = username_a
        self.username_b = username_b

    def avg_cp_loss_by_color(self):
        rows_a = {(time_class, color): avg for time_class, color, avg in db.avg_cp_loss_by_color(self.username_a, quiet=True)}
        rows_b = {(time_class, color): avg for time_class, color, avg in db.avg_cp_loss_by_color(self.username_b, quiet=True)}
        keys = sorted(set(rows_a) | set(rows_b))

        comparison = [
            (time_class, color, rows_a.get((time_class, color)), rows_b.get((time_class, color)))
            for time_class, color in keys
        ]

        for time_class, color, avg_a, avg_b in comparison:
            avg_a_str = f"{avg_a:.2f}" if avg_a is not None else "n/a"
            avg_b_str = f"{avg_b:.2f}" if avg_b is not None else "n/a"
            print(f"{self.username_a} vs {self.username_b}, {time_class}, {color}: {avg_a_str} vs {avg_b_str}")

        return comparison

    def biggest_blunders(self):
        # no shared key between the two players' blunder lists (a move in one player's
        # game has no counterpart in the other's), so pair by rank instead: 1st-worst
        # vs 1st-worst, 2nd-worst vs 2nd-worst, within each time_class.
        time_classes = sorted(
            set(db.time_classes_played(self.username_a)) | set(db.time_classes_played(self.username_b))
        )

        comparison = {}
        for time_class in time_classes:
            blunders_a = db.biggest_blunders(self.username_a, time_class, quiet=True)
            blunders_b = db.biggest_blunders(self.username_b, time_class, quiet=True)
            paired = list(zip_longest(blunders_a, blunders_b))
            comparison[time_class] = paired

            print(f"--- {time_class} ---")
            for rank, (blunder_a, blunder_b) in enumerate(paired, start=1):
                a_str = f"{blunder_a[2]} ({blunder_a[3]:.0f}cp)" if blunder_a else "—"
                b_str = f"{blunder_b[2]} ({blunder_b[3]:.0f}cp)" if blunder_b else "—"
                print(f"  #{rank}  {self.username_a}: {a_str:<18} {self.username_b}: {b_str}")

        return comparison
