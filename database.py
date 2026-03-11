"""
Database Manager for ZeroRange
Handles SQLite persistence for challenges and score history
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Database:
    """Manages SQLite database for challenges and history"""

    def __init__(self, db_path="scores.db"):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to database: {db_path}")
            self._create_tables()
            self.init_db()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            cursor = self.conn.cursor()

            # Create challenges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY,
                    module TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    points INTEGER NOT NULL,
                    completed BOOLEAN DEFAULT 0,
                    best_time INTEGER DEFAULT NULL
                )
            """)

            # Create history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    challenge_id INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    time_taken INTEGER NOT NULL,
                    FOREIGN KEY (challenge_id) REFERENCES challenges(id)
                )
            """)

            self.conn.commit()
            logger.info("Database tables created/verified")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def init_db(self):
        """Initialize database with Phase 1 challenges if empty"""
        try:
            cursor = self.conn.cursor()

            # Check if challenges already exist
            cursor.execute("SELECT COUNT(*) FROM challenges")
            count = cursor.fetchone()[0]

            if count == 0:
                # Insert all challenges: iButton, NFC, RFID, and SubGHZ
                challenges = [
                    # iButton challenges (1-3)
                    (1, 'ibutton', 'Touch & Read', 'Detect any iButton', 10, 0, None),
                    (2, 'ibutton', 'Clone iButton', 'Read then emulate', 10, 0, None),
                    (3, 'ibutton', 'Emulate Specific', 'Create custom ID', 10, 0, None),
                    # NFC challenges (4-6)
                    (4, 'nfc', 'Detect & Read', 'Detect any NFC card', 10, 0, None),
                    (5, 'nfc', 'Clone Card', 'Read and dump NFC', 10, 0, None),
                    (6, 'nfc', 'MIFARE Attack', 'Break MIFARE Classic', 10, 0, None),
                    # RFID 125kHz challenges (7-9)
                    (7, 'rfid', 'Detect Tag', 'Detect RFID 125kHz', 10, 0, None),
                    (8, 'rfid', 'Clone to T5577', 'Clone tag to T5577', 10, 0, None),
                    (9, 'rfid', 'Simulate EM410x', 'Simulate EM410x tag', 10, 0, None),
                    # SubGHZ challenges (10-12)
                    (10, 'subghz', 'Detect Signal', 'Capture RF signal', 10, 0, None),
                    (11, 'subghz', 'Record & Replay', 'Capture and replay', 10, 0, None),
                    (12, 'subghz', 'Signal Analysis', 'Analyze RF protocol', 10, 0, None),
                    # IR challenges (13-15)
                    (13, 'ir', 'Detect IR', 'Detect any IR signal', 10, 0, None),
                    (14, 'ir', 'Capture & Replay', 'Record and replay IR', 10, 0, None),
                    (15, 'ir', 'Protocol Analysis', 'Identify IR protocol', 10, 0, None)
                ]

                cursor.executemany("""
                    INSERT INTO challenges (id, module, name, description, points, completed, best_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, challenges)

                self.conn.commit()
                logger.info(f"Initialized {len(challenges)} challenges")
            elif count < 15:
                # Database exists but has fewer than 12 challenges - add missing ones
                logger.info(f"Upgrading database from {count} to 15 challenges")

                # Get existing challenge IDs
                cursor.execute("SELECT id FROM challenges")
                existing_ids = {row[0] for row in cursor.fetchall()}

                # Define all 12 challenges
                all_challenges = [
                    (1, 'ibutton', 'Touch & Read', 'Detect any iButton', 10, 0, None),
                    (2, 'ibutton', 'Clone iButton', 'Read then emulate', 10, 0, None),
                    (3, 'ibutton', 'Emulate Specific', 'Create custom ID', 10, 0, None),
                    (4, 'nfc', 'Detect & Read', 'Detect any NFC card', 10, 0, None),
                    (5, 'nfc', 'Clone Card', 'Read and dump NFC', 10, 0, None),
                    (6, 'nfc', 'MIFARE Attack', 'Break MIFARE Classic', 10, 0, None),
                    (7, 'rfid', 'Detect Tag', 'Detect RFID 125kHz', 10, 0, None),
                    (8, 'rfid', 'Clone to T5577', 'Clone tag to T5577', 10, 0, None),
                    (9, 'rfid', 'Simulate EM410x', 'Simulate EM410x tag', 10, 0, None),
                    (10, 'subghz', 'Detect Signal', 'Capture RF signal', 10, 0, None),
                    (11, 'subghz', 'Record & Replay', 'Capture and replay', 10, 0, None),
                    (12, 'subghz', 'Signal Analysis', 'Analyze RF protocol', 10, 0, None),
                    (13, 'ir', 'Detect IR', 'Detect any IR signal', 10, 0, None),
                    (14, 'ir', 'Capture & Replay', 'Record and replay IR', 10, 0, None),
                    (15, 'ir', 'Protocol Analysis', 'Identify IR protocol', 10, 0, None)
                ]

                # Add only missing challenges
                missing_challenges = [ch for ch in all_challenges if ch[0] not in existing_ids]

                if missing_challenges:
                    cursor.executemany("""
                        INSERT INTO challenges (id, module, name, description, points, completed, best_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, missing_challenges)
                    self.conn.commit()
                    logger.info(f"Added {len(missing_challenges)} new challenges")
            else:
                logger.info(f"Database already contains {count} challenges (max: 15)")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_total_score(self) -> int:
        """
        Get total score (sum of points from completed challenges)

        Returns:
            int: Total score
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT SUM(points) FROM challenges WHERE completed = 1
            """)
            result = cursor.fetchone()[0]
            return result if result is not None else 0

        except Exception as e:
            logger.error(f"Failed to get total score: {e}")
            return 0

    def get_challenge_status(self, challenge_id: int) -> Optional[Dict]:
        """
        Get status of specific challenge

        Args:
            challenge_id: Challenge ID (1-3 for Phase 1)

        Returns:
            dict: {completed: bool, points: int, best_time: int|None}
                  or None if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT completed, points, best_time
                FROM challenges
                WHERE id = ?
            """, (challenge_id,))

            row = cursor.fetchone()
            if row:
                return {
                    'completed': bool(row['completed']),
                    'points': row['points'],
                    'best_time': row['best_time']
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get challenge status: {e}")
            return None

    def get_all_challenges(self) -> List[Dict]:
        """
        Get all challenges with their status

        Returns:
            list: List of challenge dicts with all fields
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, module, name, description, points, completed, best_time
                FROM challenges
                ORDER BY id
            """)

            challenges = []
            for row in cursor.fetchall():
                challenges.append({
                    'id': row['id'],
                    'module': row['module'],
                    'name': row['name'],
                    'description': row['description'],
                    'points': row['points'],
                    'completed': bool(row['completed']),
                    'best_time': row['best_time']
                })

            return challenges

        except Exception as e:
            logger.error(f"Failed to get challenges: {e}")
            return []

    def mark_completed(self, challenge_id: int, time_taken: int):
        """
        Mark challenge as completed and update best time if applicable

        Args:
            challenge_id: Challenge ID
            time_taken: Time taken in seconds
        """
        try:
            cursor = self.conn.cursor()

            # Get current best time
            cursor.execute("""
                SELECT best_time FROM challenges WHERE id = ?
            """, (challenge_id,))

            row = cursor.fetchone()
            if row is None:
                logger.warning(f"Challenge {challenge_id} not found")
                return

            current_best = row['best_time']

            # Update best time if this is better (or first completion)
            if current_best is None or time_taken < current_best:
                cursor.execute("""
                    UPDATE challenges
                    SET completed = 1, best_time = ?
                    WHERE id = ?
                """, (time_taken, challenge_id))
                logger.info(f"Challenge {challenge_id} completed in {time_taken}s (new best)")
            else:
                cursor.execute("""
                    UPDATE challenges
                    SET completed = 1
                    WHERE id = ?
                """, (challenge_id,))
                logger.info(f"Challenge {challenge_id} completed in {time_taken}s")

            self.conn.commit()

        except Exception as e:
            logger.error(f"Failed to mark challenge completed: {e}")

    def add_history(self, challenge_id: int, success: bool, time_taken: int):
        """
        Add attempt to history

        Args:
            challenge_id: Challenge ID
            success: True if completed successfully
            time_taken: Time taken in seconds
        """
        try:
            cursor = self.conn.cursor()

            timestamp = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO history (timestamp, challenge_id, success, time_taken)
                VALUES (?, ?, ?, ?)
            """, (timestamp, challenge_id, success, time_taken))

            self.conn.commit()
            logger.info(f"Added history: Challenge {challenge_id}, success={success}, time={time_taken}s")

        except Exception as e:
            logger.error(f"Failed to add history: {e}")

    def get_stats(self) -> Dict:
        """
        Get overall statistics

        Returns:
            dict: {
                total_score: int,
                completed_count: int,
                total_challenges: int,
                total_attempts: int,
                success_rate: float
            }
        """
        try:
            cursor = self.conn.cursor()

            # Get total score
            total_score = self.get_total_score()

            # Get completed count
            cursor.execute("SELECT COUNT(*) FROM challenges WHERE completed = 1")
            completed_count = cursor.fetchone()[0]

            # Get total challenges
            cursor.execute("SELECT COUNT(*) FROM challenges")
            total_challenges = cursor.fetchone()[0]

            # Get total attempts
            cursor.execute("SELECT COUNT(*) FROM history")
            total_attempts = cursor.fetchone()[0]

            # Get success count
            cursor.execute("SELECT COUNT(*) FROM history WHERE success = 1")
            success_count = cursor.fetchone()[0]

            # Calculate success rate
            success_rate = (success_count / total_attempts * 100) if total_attempts > 0 else 0

            return {
                'total_score': total_score,
                'completed_count': completed_count,
                'total_challenges': total_challenges,
                'total_attempts': total_attempts,
                'success_rate': success_rate
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'total_score': 0,
                'completed_count': 0,
                'total_challenges': 0,
                'total_attempts': 0,
                'success_rate': 0
            }

    def reset_scores(self):
        """Reset all scores and clear history"""
        try:
            cursor = self.conn.cursor()

            # Reset challenges
            cursor.execute("""
                UPDATE challenges
                SET completed = 0, best_time = NULL
            """)

            # Clear history
            cursor.execute("DELETE FROM history")

            self.conn.commit()
            logger.info("All scores reset and history cleared")

        except Exception as e:
            logger.error(f"Failed to reset scores: {e}")

    def close(self):
        """Close database connection"""
        try:
            self.conn.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Failed to close database: {e}")


# Test code for standalone testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )

    print("Testing Database class...")

    # Create test database
    db = Database("test_scores.db")

    # Display all challenges
    print("\nAll challenges:")
    challenges = db.get_all_challenges()
    for ch in challenges:
        print(f"  {ch['id']}: {ch['name']} - {ch['points']}pts - Completed: {ch['completed']}")

    # Test adding history and marking completed
    print("\nSimulating Challenge 1 success...")
    db.add_history(1, True, 45)
    db.mark_completed(1, 45)

    print("\nSimulating Challenge 2 fail...")
    db.add_history(2, False, 90)

    print("\nSimulating Challenge 1 again (better time)...")
    db.add_history(1, True, 30)
    db.mark_completed(1, 30)

    # Get stats
    print("\nStatistics:")
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print(f"\nTotal Score: {db.get_total_score()}/40")

    # Get specific challenge status
    print("\nChallenge 1 status:")
    status = db.get_challenge_status(1)
    if status:
        print(f"  Completed: {status['completed']}")
        print(f"  Best time: {status['best_time']}s")

    db.close()
    print("\nDatabase test complete!")
