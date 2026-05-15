from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.order import Order
from app.models.sales_goal import SalesGoal


def get_sales_performance(db: Session, seller_id: int):
    now = datetime.utcnow()
    year = now.year
    month = now.month

    goal = db.query(SalesGoal).filter_by(seller_id=seller_id, year=year, month=month).first()

    total_sales = db.query(func.sum(Order.total_net)).filter(
        Order.seller_id == seller_id,
        func.extract('month', Order.created_at) == month,
        func.extract('year', Order.created_at) == year
    ).scalar() or 0

    total_orders = db.query(func.count(Order.id)).filter(
        Order.seller_id == seller_id,
        func.extract('month', Order.created_at) == month,
        func.extract('year', Order.created_at) == year
    ).scalar() or 0

    goal_value = goal.goal_value if goal else 0
    percent = (total_sales / goal_value * 100) if goal_value > 0 else 0

    return {
        "goal": goal_value,
        "sales": total_sales,
        "orders": total_orders,
        "percent": round(percent, 2)
    }
