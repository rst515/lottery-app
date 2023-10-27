from app.models import BonusBall

for i in range(1,60):
    BonusBall.objects.create(ball_id=i)
