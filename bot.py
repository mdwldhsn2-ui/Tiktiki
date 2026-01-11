import telebot
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# কনফিগারেশন
# ==========================================
BOT_TOKEN = '8471158487:AAE3Ju0nqO3Nhxt_-t0foVbUv8e1dbhb88g'  # এখানে আপনার টোকেন দিন
bot = telebot.TeleBot(BOT_TOKEN)

# ইউজারের কুকিজ মেমোরিতে রাখার জন্য (Render এ ফাইল সেভ করা রিস্কি কারণ রিস্টার্ট হলে মুছে যায়)
user_cookies = {}

# ==========================================
# ব্রাউজার সেটআপ (Render/Server Friendly)
# ==========================================
def get_driver():
    chrome_options = Options()
    
    # সার্ভারের জন্য জরুরি সেটিংস
    chrome_options.add_argument("--headless")  # ডিসপ্লে ছাড়া রান হবে
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage") # মেমোরি ক্র্যাশ ঠেকাবে
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # TikTok ব্লক এড়াতে ইউজার এজেন্ট চেঞ্জ করা
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # অটোমেটিক ড্রাইভার ইনস্টল এবং রান
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# ==========================================
# বট কমান্ড হ্যান্ডলার
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message)
    welcome_text = (
        "🤖 **TikTok Auto Bot Active!**\n\n"
        "ধাপ ১: আপনার TikTok লগইন করা ব্রাউজার থেকে কুকিজ (JSON) ফাইল আমাকে পাঠান।\n"
        "ধাপ ২: কুকি সেট হলে ভিডিওর লিংক দিলে আমি লাইক দেব।"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ১. কুকিজ ফাইল রিসিভ করা
@bot.message_handler(content_types=['document'])
def handle_cookies(message):
    try:
        if message.document.mime_type == 'application/json' or message.document.file_name.endswith('.json'):
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # JSON লোড করা
            cookies = json.loads(downloaded_file)
            user_cookies[message.chat.id] = cookies
            
            bot.reply_to(message, "✅ Cookies লোড হয়েছে! এখন TikTok ভিডিওর লিংক দিন।")
        else:
            bot.reply_to(message, "❌ দয়া করে সঠিক JSON ফাইল দিন।")
    except Exception as e:
        bot.reply_to(message, f"❌ কুকি লোড করতে সমস্যা হয়েছে: {str(e)}")

# ২. লিংক রিসিভ এবং লাইক দেওয়া
@bot.message_handler(func=lambda message: "tiktok.com" in message.text)
def process_link(message):
    chat_id = message.chat.id
    url = message.text

    # চেক করা কুকি আছে কি না
    if chat_id not in user_cookies:
        bot.reply_to(message, "⚠️ লাইক দেওয়ার আগে কুকিজ ফাইল আপলোড করুন।")
        return

    status_msg = bot.reply_to(message, "⏳ প্রসেসিং চলছে... (TikTok লোড হচ্ছে)")

    driver = None
    try:
        driver = get_driver()
        
        # ১. প্রথমে ডোমেইনে যাওয়া (কুকি সেট করার জন্য)
        driver.get("https://www.tiktok.com")
        
        # ২. কুকিজ ইনজেক্ট করা
        cookies = user_cookies[chat_id]
        for cookie in cookies:
            try:
                driver.add_cookie({
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': '.tiktok.com',
                    'path': '/'
                })
            except:
                pass # কিছু কুকি ফেইল করতে পারে, সমস্যা নেই
        
        # ৩. পেজ রিফ্রেশ করে লগইন নিশ্চিত করা
        driver.refresh()
        
        # ৪. টার্গেট ভিডিওতে যাওয়া
        driver.get(url)
        time.sleep(5) # পেজ লোড টাইম
        
        # ৫. লাইক বাটন খোঁজা এবং ক্লিক করা
        try:
            # TikTok-এর লাইক বাটন খোঁজার জন্য সেরা সিলেক্টর (XPath)
            # নোট: ক্লাস নেম চেঞ্জ হতে পারে, তাই data-e2e অ্যাট্রিবিউট ব্যবহার করা হলো
            like_xpath = "//span[@data-e2e='like-icon']"
            
            wait = WebDriverWait(driver, 10)
            like_btn = wait.until(EC.presence_of_element_located((By.XPATH, like_xpath)))
            
            # সাধারণ ক্লিক কাজ না করলে জাভাস্ক্রিপ্ট দিয়ে ক্লিক করা
            driver.execute_script("arguments[0].click();", like_btn)
            
            bot.edit_message_text(f"✅ সফল! লাইক দেওয়া হয়েছে।\n🔗 {url}", chat_id, status_msg.message_id)
            
        except Exception as e:
            bot.edit_message_text("❌ লাইক বাটন পাওয়া যায়নি। হয়তো ভিডিওটি নেই বা লগইন ফেইল করেছে।", chat_id, status_msg.message_id)
            print(f"Error finding button: {e}")

    except Exception as e:
        bot.edit_message_text(f"❌ সিস্টেম এরর: {str(e)}", chat_id, status_msg.message_id)
    
    finally:
        # মেমোরি বাঁচাতে অবশ্যই ব্রাউজার বন্ধ করতে হবে
        if driver:
            driver.quit()

# বট চালু রাখা
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()_data[day] = {"Morning": morning.strip(), "Night": night.strip()}
        
        if not new_week_data:
            await update.message.reply_text("⚠️ ফরম্যাট ভুল।")
            return

        user_ref = db.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()
        current_routine = user_data.get('routine', {})
        if week_name not in current_routine: current_routine[week_name] = {}
        current_routine[week_name].update(new_week_data)
        user_ref.update({'routine': current_routine})
        
        await update.message.reply_text(f"✅ সফল! **{week_name}** যুক্ত হয়েছে।")
        await send_routine(update, context, user_id)
    except Exception as e:
        await update.message.reply_text("⚠️ কিছু ভুল হয়েছে।")

# --- ৫. ডিলিট কমান্ড ---
async def delete_routine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.replace("/delete ", "")
    try:
        week, day = [p.strip() for p in text.split(',')]
        user_ref = db.collection('users').document(user_id)
        user_data = user_ref.get().to_dict()
        current_routine = user_data.get('routine', {})
        if week in current_routine and day in current_routine[week]:
            del current_routine[week][day]
            user_ref.update({'routine': current_routine})
            await update.message.reply_text(f"🗑️ {week} - {day} মুছে ফেলা হয়েছে।")
            await send_routine(update, context, user_id)
        else: await update.message.reply_text("⚠️ রুটিন পাওয়া যায়নি।")
    except: await update.message.reply_text("ব্যবহার: `/delete Week 1, Saturday`", parse_mode='Markdown')

# --- মেইন রানার ---
if __name__ == '__main__':
    keep_alive()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("addweek", add_bulk_routine))
    app_bot.add_handler(CommandHandler("delete", delete_routine))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    print("Bot Started...")
    app_bot.run_polling()