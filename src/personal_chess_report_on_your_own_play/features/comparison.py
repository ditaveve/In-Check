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

    def opening_matchups(self, min_frequency=0.15):
        # Same-color comparison (white vs white, black vs black) doesn't reflect how a real
        # game goes -- it never tells you whether the *opponent* can actually handle what you
        # throw at them. What matters is cross-color: what one player plays as White against
        # what the other player has actually faced as Black, in both directions. A family the
        # White side leans on but the Black side has zero experience with is the real signal;
        # how often the Black side *also* plays that family as White is irrelevant here.
        rows_a = {
            (color, family): freq
            for color, family, n, freq in db.opening_frequency(self.username_a, quiet=True)
        }
        rows_b = {
            (color, family): freq
            for color, family, n, freq in db.opening_frequency(self.username_b, quiet=True)
        }

        def matchup(white_user, white_rows, black_user, black_rows):
            white_families = sorted(
                ((family, freq) for (color, family), freq in white_rows.items()
                 if color == 'white' and freq >= min_frequency),
                key=lambda item: item[1], reverse=True
            )
            print(f"=== {white_user} as White vs {black_user} as Black ===")
            if not any(color == 'black' for color, _ in black_rows):
                print(f"  (not enough {black_user} Black games to say anything reliable)")
                return []

            results = []
            for family, white_freq in white_families:
                black_freq = black_rows.get(('black', family))
                results.append((family, white_freq, black_freq))
                if black_freq is None:
                    print(f"  family {family}: {white_user} plays it {white_freq:.0%} as White -- {black_user} has never played Black against it")
                else:
                    print(f"  family {family}: {white_user} plays it {white_freq:.0%} as White -- {black_user} has faced it {black_freq:.0%} of their Black games")
            return results

        a_vs_b = matchup(self.username_a, rows_a, self.username_b, rows_b)
        b_vs_a = matchup(self.username_b, rows_b, self.username_a, rows_a)

        return {
            f"{self.username_a}_white_vs_{self.username_b}_black": a_vs_b,
            f"{self.username_b}_white_vs_{self.username_a}_black": b_vs_a,
        }

    def biggest_blunders(self):

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
