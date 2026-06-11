from collections import defaultdict

from app.domain.models import Activity, BreakdownItem, SummaryStats, UserSweatStatistics


class SweatStatisticsService:
    def calculate_statistics(self, activities: list[Activity]) -> UserSweatStatistics:
        # Filter for completed activities with valid sweat rate calculations
        valid_activities = [
            a for a in activities if a.total_sweat_loss_ml is not None and a.sweat_rate_ml_per_hour is not None
        ]

        if not valid_activities:
            return UserSweatStatistics(
                summary=SummaryStats(overall_avg_sweat_rate_ml_h=0.0, total_activities_logged=0),
                breakdowns={"sport": [], "environment": [], "clothing": []},
            )

        # 1. Overall Calculations
        total_activities = len(valid_activities)
        overall_avg_rate = round(
            sum(a.sweat_rate_ml_per_hour for a in valid_activities if a.sweat_rate_ml_per_hour is not None)
            / total_activities,
            2,
        )
        summary = SummaryStats(
            overall_avg_sweat_rate_ml_h=overall_avg_rate,
            total_activities_logged=total_activities,
        )

        breakdowns: dict[str, list[BreakdownItem]] = {}

        # 2. Sport Breakdown
        sport_groups: dict[str, list[Activity]] = defaultdict(list)
        for a in valid_activities:
            sport_groups[a.activity_type].append(a)

        sport_items = []
        for sport, acts in sport_groups.items():
            rates = [a.sweat_rate_ml_per_hour for a in acts if a.sweat_rate_ml_per_hour is not None]
            avg_rate = round(sum(rates) / len(rates), 2) if rates else 0.0
            sport_items.append(
                BreakdownItem(
                    key=sport.lower(),
                    display_name=sport,
                    avg_sweat_rate_ml_h=avg_rate,
                    activity_count=len(acts),
                )
            )
        breakdowns["sport"] = sorted(sport_items, key=lambda x: x.activity_count, reverse=True)

        # 3. Environment/Temperature Breakdown
        temp_groups: dict[str, list[Activity]] = {"cold": [], "moderate": [], "hot": []}
        for a in valid_activities:
            temp = a.temp_celsius_user if a.temp_celsius_user is not None else a.temp_celsius_api
            if temp is None:
                continue
            if temp < 10.0:
                temp_groups["cold"].append(a)
            elif temp <= 20.0:
                temp_groups["moderate"].append(a)
            else:
                temp_groups["hot"].append(a)

        display_names = {
            "cold": "Cold (< 10°C)",
            "moderate": "Moderate (10°C - 20°C)",
            "hot": "Hot (> 20°C)",
        }
        env_items = []
        for category, acts in temp_groups.items():
            if not acts:
                continue
            rates = [a.sweat_rate_ml_per_hour for a in acts if a.sweat_rate_ml_per_hour is not None]
            avg_rate = round(sum(rates) / len(rates), 2) if rates else 0.0
            env_items.append(
                BreakdownItem(
                    key=category,
                    display_name=display_names[category],
                    avg_sweat_rate_ml_h=avg_rate,
                    activity_count=len(acts),
                )
            )
        breakdowns["environment"] = env_items

        # 4. Clothing Breakdown
        clothing_groups: dict[int, list[Activity]] = defaultdict(list)
        for a in valid_activities:
            if a.clothing_index_user is not None:
                clothing_groups[a.clothing_index_user].append(a)

        clothing_display = {1: "Minimal", 2: "Standard", 3: "Layers"}
        clothing_items = []
        for idx, acts in clothing_groups.items():
            rates = [a.sweat_rate_ml_per_hour for a in acts if a.sweat_rate_ml_per_hour is not None]
            avg_rate = round(sum(rates) / len(rates), 2) if rates else 0.0
            clothing_items.append(
                BreakdownItem(
                    key=str(idx),
                    display_name=clothing_display.get(idx, f"Index {idx}"),
                    avg_sweat_rate_ml_h=avg_rate,
                    activity_count=len(acts),
                )
            )
        breakdowns["clothing"] = sorted(clothing_items, key=lambda x: x.key)

        return UserSweatStatistics(summary=summary, breakdowns=breakdowns)
