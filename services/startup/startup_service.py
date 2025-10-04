from services.fotmob.fotmob_service import FotMobService
from apscheduler.schedulers.background import BackgroundScheduler

from services.whoscored.whoscored_service import WhoScoredService

class StartupService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def update_fotmob_fixtures(self):
        leagues = ["ENG-Premier League"]  # 🔧 extend later
        for league in leagues:
            FotMobService(league).get_fixtures()

    def update_whoscored_fixtures(self):
        leagues = ["ENG-Premier League"]  # 🔧 extend later
        for league in leagues:
            WhoScoredService(league).get_fixtures()

    async def start(self):
        # Run immediately on startup
        self.update_fotmob_fixtures()
        self.update_whoscored_fixtures()

        # Schedule daily jobs
        self.scheduler.add_job(self.update_fotmob_fixtures, "cron", hour=0, minute=0, timezone="UTC")
        self.scheduler.add_job(self.update_whoscored_fixtures, "cron", hour=0, minute=5, timezone="UTC")
        # ^ small offset to avoid hammering both at exact same second

        self.scheduler.start()
        print("🚀 StartupService: scheduler started")

    async def stop(self):
        self.scheduler.shutdown()
        print("🛑 StartupService: scheduler stopped")