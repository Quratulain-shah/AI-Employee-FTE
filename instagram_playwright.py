#!/usr/bin/env python3
"""
Instagram Playwright Automation
Posts images/reels, sends DMs, and monitors activity using Playwright
No API needed - uses browser automation
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InstagramPlaywright:
    """Instagram automation using Playwright - no API required"""

    def __init__(self):
        self.session_path = os.getenv('INSTAGRAM_SESSION_PATH', './instagram_session')
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        self.browser = None
        self.context = None
        self.page = None

        Path(self.session_path).mkdir(parents=True, exist_ok=True)

    async def _init_browser(self, headless: bool = False):
        """Initialize browser with persistent context"""
        try:
            from playwright.async_api import async_playwright

            self.playwright = await async_playwright().start()

            self.context = await self.playwright.chromium.launch_persistent_context(
                self.session_path,
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled'
                ],
                viewport={'width': 430, 'height': 932},  # Mobile viewport
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
            )

            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            logger.info("Browser initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to init browser: {e}")
            return False

    async def _close_browser(self):
        """Close browser"""
        try:
            if self.context:
                await self.context.close()
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def _check_login(self) -> bool:
        """Check if logged into Instagram"""
        try:
            await self.page.goto('https://www.instagram.com/', wait_until='domcontentloaded')
            await self.page.wait_for_timeout(3000)

            # Check for login form
            login_form = await self.page.query_selector('input[name="username"]')
            if login_form:
                return False

            # Check for home feed elements
            home = await self.page.query_selector('svg[aria-label="Home"]')
            return home is not None

        except Exception as e:
            logger.error(f"Error checking login: {e}")
            return False

    async def login(self, username: str = None, password: str = None) -> Dict[str, Any]:
        """
        Login to Instagram

        Args:
            username: Instagram username
            password: Instagram password
        """
        try:
            username = username or self.username
            password = password or self.password

            if not username or not password:
                return {"success": False, "error": "Credentials not provided"}

            if not await self._init_browser():
                return {"success": False, "error": "Failed to init browser"}

            await self.page.goto('https://www.instagram.com/accounts/login/')
            await self.page.wait_for_timeout(3000)

            # Fill credentials
            await self.page.fill('input[name="username"]', username)
            await self.page.fill('input[name="password"]', password)
            await self.page.wait_for_timeout(500)

            # Click login
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_timeout(5000)

            # Handle "Save Login Info" popup
            try:
                not_now = self.page.locator('text="Not Now"').first
                if await not_now.is_visible():
                    await not_now.click()
            except:
                pass

            # Handle notifications popup
            try:
                not_now = self.page.locator('text="Not Now"').first
                if await not_now.is_visible():
                    await not_now.click()
            except:
                pass

            await self.page.wait_for_timeout(2000)

            if await self._check_login():
                logger.info("Instagram login successful")
                await self._close_browser()
                return {"success": True, "username": username}
            else:
                await self._close_browser()
                return {"success": False, "error": "Login failed - check credentials or 2FA"}

        except Exception as e:
            logger.error(f"Login error: {e}")
            await self._close_browser()
            return {"success": False, "error": str(e)}

    async def post_image(self, image_path: str, caption: str) -> Dict[str, Any]:
        """
        Post an image to Instagram

        Args:
            image_path: Path to image file
            caption: Post caption
        """
        try:
            if not Path(image_path).exists():
                return {"success": False, "error": f"Image not found: {image_path}"}

            if not await self._init_browser():
                return {"success": False, "error": "Failed to init browser"}

            if not await self._check_login():
                logger.warning("Not logged in, attempting login...")
                login_result = await self.login()
                if not login_result.get('success'):
                    await self._close_browser()
                    return {"success": False, "error": "Not logged in"}
                await self._init_browser()

            # Go to Instagram
            await self.page.goto('https://www.instagram.com/')
            await self.page.wait_for_timeout(3000)

            # Click create post button (+ icon)
            create_btn = self.page.locator('svg[aria-label="New post"]').first
            await create_btn.click()
            await self.page.wait_for_timeout(2000)

            # Upload file
            file_input = self.page.locator('input[type="file"]').first
            await file_input.set_input_files(str(Path(image_path).absolute()))
            await self.page.wait_for_timeout(3000)

            # Click Next (crop)
            next_btn = self.page.locator('text="Next"').first
            await next_btn.click()
            await self.page.wait_for_timeout(2000)

            # Click Next (filters)
            await next_btn.click()
            await self.page.wait_for_timeout(2000)

            # Add caption
            caption_input = self.page.locator('textarea[aria-label="Write a caption..."]').first
            await caption_input.fill(caption)
            await self.page.wait_for_timeout(1000)

            # Share
            share_btn = self.page.locator('text="Share"').first
            await share_btn.click()
            await self.page.wait_for_timeout(5000)

            logger.info("Image posted successfully")
            await self._close_browser()

            return {
                "success": True,
                "platform": "instagram",
                "type": "image",
                "caption": caption[:50] + "..." if len(caption) > 50 else caption,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Post failed: {e}")
            await self._close_browser()
            return {"success": False, "error": str(e)}

    async def post_story(self, image_path: str) -> Dict[str, Any]:
        """
        Post a story to Instagram

        Args:
            image_path: Path to image/video file
        """
        try:
            if not Path(image_path).exists():
                return {"success": False, "error": f"File not found: {image_path}"}

            if not await self._init_browser():
                return {"success": False, "error": "Failed to init browser"}

            if not await self._check_login():
                await self._close_browser()
                return {"success": False, "error": "Not logged in"}

            await self.page.goto('https://www.instagram.com/')
            await self.page.wait_for_timeout(3000)

            # Click on profile/story icon to add story
            story_btn = self.page.locator('svg[aria-label="New story"]').first
            await story_btn.click()
            await self.page.wait_for_timeout(2000)

            # Upload file
            file_input = self.page.locator('input[type="file"]').first
            await file_input.set_input_files(str(Path(image_path).absolute()))
            await self.page.wait_for_timeout(3000)

            # Share to story
            share_btn = self.page.locator('text="Share to Story"').first
            await share_btn.click()
            await self.page.wait_for_timeout(3000)

            logger.info("Story posted successfully")
            await self._close_browser()

            return {
                "success": True,
                "platform": "instagram",
                "type": "story",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Story post failed: {e}")
            await self._close_browser()
            return {"success": False, "error": str(e)}

    async def send_dm(self, username: str, message: str) -> Dict[str, Any]:
        """
        Send a direct message

        Args:
            username: Recipient username
            message: Message text
        """
        try:
            if not await self._init_browser():
                return {"success": False, "error": "Failed to init browser"}

            if not await self._check_login():
                await self._close_browser()
                return {"success": False, "error": "Not logged in"}

            # Go to DMs
            await self.page.goto('https://www.instagram.com/direct/inbox/')
            await self.page.wait_for_timeout(3000)

            # Click new message
            new_msg = self.page.locator('svg[aria-label="New message"]').first
            await new_msg.click()
            await self.page.wait_for_timeout(2000)

            # Search for user
            search_input = self.page.locator('input[placeholder="Search..."]').first
            await search_input.fill(username)
            await self.page.wait_for_timeout(2000)

            # Select user from results
            user_result = self.page.locator(f'text="{username}"').first
            await user_result.click()
            await self.page.wait_for_timeout(1000)

            # Click Next/Chat
            next_btn = self.page.locator('text="Chat"').first
            await next_btn.click()
            await self.page.wait_for_timeout(2000)

            # Type message
            msg_input = self.page.locator('textarea[placeholder="Message..."]').first
            await msg_input.fill(message)
            await self.page.wait_for_timeout(500)

            # Send
            send_btn = self.page.locator('text="Send"').first
            await send_btn.click()
            await self.page.wait_for_timeout(2000)

            logger.info(f"DM sent to {username}")
            await self._close_browser()

            return {
                "success": True,
                "platform": "instagram",
                "type": "dm",
                "to": username,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"DM failed: {e}")
            await self._close_browser()
            return {"success": False, "error": str(e)}

    async def get_notifications(self) -> Dict[str, Any]:
        """Get recent notifications"""
        try:
            if not await self._init_browser():
                return {"success": False, "error": "Failed to init browser"}

            if not await self._check_login():
                await self._close_browser()
                return {"success": False, "error": "Not logged in"}

            # Go to notifications
            await self.page.goto('https://www.instagram.com/')
            await self.page.wait_for_timeout(2000)

            # Click notifications
            notif_btn = self.page.locator('svg[aria-label="Notifications"]').first
            await notif_btn.click()
            await self.page.wait_for_timeout(2000)

            # Get notification items
            notifications = []
            notif_items = await self.page.query_selector_all('[role="button"]')

            for item in notif_items[:10]:
                try:
                    text = await item.inner_text()
                    if text and len(text) > 10:
                        notifications.append({"text": text[:100]})
                except:
                    continue

            await self._close_browser()

            return {
                "success": True,
                "count": len(notifications),
                "notifications": notifications
            }

        except Exception as e:
            logger.error(f"Get notifications failed: {e}")
            await self._close_browser()
            return {"success": False, "error": str(e)}

    async def follow_user(self, username: str) -> Dict[str, Any]:
        """Follow a user"""
        try:
            if not await self._init_browser():
                return {"success": False, "error": "Failed to init browser"}

            if not await self._check_login():
                await self._close_browser()
                return {"success": False, "error": "Not logged in"}

            # Go to user profile
            await self.page.goto(f'https://www.instagram.com/{username}/')
            await self.page.wait_for_timeout(3000)

            # Click follow button
            follow_btn = self.page.locator('text="Follow"').first
            if await follow_btn.is_visible():
                await follow_btn.click()
                await self.page.wait_for_timeout(2000)

                logger.info(f"Followed {username}")
                await self._close_browser()
                return {"success": True, "action": "follow", "username": username}
            else:
                await self._close_browser()
                return {"success": False, "error": "Already following or user not found"}

        except Exception as e:
            logger.error(f"Follow failed: {e}")
            await self._close_browser()
            return {"success": False, "error": str(e)}

    async def like_post(self, post_url: str) -> Dict[str, Any]:
        """Like a post by URL"""
        try:
            if not await self._init_browser():
                return {"success": False, "error": "Failed to init browser"}

            if not await self._check_login():
                await self._close_browser()
                return {"success": False, "error": "Not logged in"}

            await self.page.goto(post_url)
            await self.page.wait_for_timeout(3000)

            # Click like button
            like_btn = self.page.locator('svg[aria-label="Like"]').first
            if await like_btn.is_visible():
                await like_btn.click()
                await self.page.wait_for_timeout(1000)

                logger.info(f"Liked post: {post_url}")
                await self._close_browser()
                return {"success": True, "action": "like", "url": post_url}
            else:
                await self._close_browser()
                return {"success": False, "error": "Already liked or post not found"}

        except Exception as e:
            logger.error(f"Like failed: {e}")
            await self._close_browser()
            return {"success": False, "error": str(e)}

    def queue_post(self, image_path: str, caption: str, schedule_time: str = None) -> Dict[str, Any]:
        """Queue a post for later"""
        try:
            queue_dir = Path("Pending_Approval/Instagram")
            queue_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"INSTAGRAM_POST_{timestamp}.md"
            filepath = queue_dir / filename

            content = f"""---
type: instagram_post
image_path: {image_path}
schedule_time: {schedule_time or 'immediate'}
status: pending_approval
created_at: {datetime.now().isoformat()}
---

# Instagram Post Draft

**Image:** {image_path}

## Caption

{caption}

---

## Actions
- [ ] Review content
- [x] Approve (move to Approved folder)
- [ ] Reject
"""
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Post queued: {filepath}")

            return {
                "success": True,
                "queue_file": str(filepath),
                "scheduled": schedule_time
            }

        except Exception as e:
            logger.error(f"Queue failed: {e}")
            return {"success": False, "error": str(e)}


# Sync wrappers
def post_image_sync(image_path: str, caption: str) -> Dict[str, Any]:
    ig = InstagramPlaywright()
    return asyncio.run(ig.post_image(image_path, caption))

def send_dm_sync(username: str, message: str) -> Dict[str, Any]:
    ig = InstagramPlaywright()
    return asyncio.run(ig.send_dm(username, message))


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Instagram Playwright Automation')
    parser.add_argument('action', choices=[
        'login', 'post', 'story', 'dm', 'follow', 'like', 'notifications', 'queue'
    ])
    parser.add_argument('--username', help='Instagram username or target user')
    parser.add_argument('--password', help='Instagram password')
    parser.add_argument('--image', help='Image path')
    parser.add_argument('--caption', help='Post caption')
    parser.add_argument('--message', help='DM message')
    parser.add_argument('--url', help='Post URL')
    parser.add_argument('--schedule', help='Schedule time')

    args = parser.parse_args()

    try:
        ig = InstagramPlaywright()

        if args.action == 'login':
            result = asyncio.run(ig.login(args.username, args.password))
        elif args.action == 'post':
            if not args.image or not args.caption:
                print(json.dumps({"error": "--image and --caption required"}))
                sys.exit(1)
            result = asyncio.run(ig.post_image(args.image, args.caption))
        elif args.action == 'story':
            if not args.image:
                print(json.dumps({"error": "--image required"}))
                sys.exit(1)
            result = asyncio.run(ig.post_story(args.image))
        elif args.action == 'dm':
            if not args.username or not args.message:
                print(json.dumps({"error": "--username and --message required"}))
                sys.exit(1)
            result = asyncio.run(ig.send_dm(args.username, args.message))
        elif args.action == 'follow':
            if not args.username:
                print(json.dumps({"error": "--username required"}))
                sys.exit(1)
            result = asyncio.run(ig.follow_user(args.username))
        elif args.action == 'like':
            if not args.url:
                print(json.dumps({"error": "--url required"}))
                sys.exit(1)
            result = asyncio.run(ig.like_post(args.url))
        elif args.action == 'notifications':
            result = asyncio.run(ig.get_notifications())
        elif args.action == 'queue':
            if not args.image or not args.caption:
                print(json.dumps({"error": "--image and --caption required"}))
                sys.exit(1)
            result = ig.queue_post(args.image, args.caption, args.schedule)

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
