from instagrapi import Client
import json, time, random, os

DOC_ID = "29088580780787855"
FINAL_FILE = "final.json"

action_counter = 0
next_human_wait = random.randint(40, 50)
human_wait_happened = False


def maybe_human_wait():
    global action_counter, next_human_wait, human_wait_happened
    action_counter += 1
    if action_counter >= next_human_wait:
        idle = random.randint(120, 200)
        print("😴 WAITING :", idle, "seconds")
        time.sleep(idle)
        action_counter = 0
        next_human_wait = random.randint(20, 30)
        human_wait_happened = True


def fixed_delay():
    global human_wait_happened
    if human_wait_happened:
        human_wait_happened = False
        return
    time.sleep(random.randint(30, 40))


def build_headers(tid, csrftoken):
    return {
        "User-Agent": "Mozilla/5.0",
        "X-CSRFToken": csrftoken,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.instagram.com/direct/t/{tid}/"
    }


def change_title(cl, headers, cookies, tid, title):
    try:
        cl.private.headers.update(headers)
        cl.private.cookies.update(cookies)
        payload = {
            "doc_id": DOC_ID,
            "variables": json.dumps({"thread_fbid": tid, "new_title": title})
        }
        cl.private.post("https://www.instagram.com/api/graphql/", data=payload)
        print(cl.username, "RENAMED ✅ ", tid)
        maybe_human_wait()
    except Exception as e:
        print(cl.username, "⚠️ RENAME FAILED — SKIPPING ➡️", tid, "|", e)


def send_msg(cl, tid, text):
    try:
        cl.direct_send(text, thread_ids=[tid])
        print(cl.username, "️ SENT 📨 ️", tid)
        maybe_human_wait()
        return True
    except Exception as e:
        print(cl.username, "⚠️ SEND FAILED — SKIPPING ➡️", tid, "|", e)
        return False


texts = open("texts.txt", "r", encoding="utf-8").read().split(";")
renames = [r.strip() for r in open("renames.txt", "r", encoding="utf-8") if r.strip()]

clients = []

if not os.path.exists(FINAL_FILE):
    print("❌ final.json not found. Run manage.py first")
    exit()

data = json.load(open(FINAL_FILE, "r", encoding="utf-8"))
accounts = data.get("accounts", [])

for acc in accounts:
    try:
        cl = Client()
        cl.set_device(acc["device"])
        cl.login_by_sessionid(acc["sessionid"])
        cl.private.cookies.update(acc["cookies"])

        print("⚡ LOGGED IN AS ➡️ ", cl.username)

        clients.append({
            "cl": cl,
            "threads": acc.get("threads", []),
            "csrftoken": acc["csrftoken"],
            "cookies": acc["cookies"]
        })

    except Exception as e:
        print("⚠️ LOGIN FAILED — SKIPPING ACCOUNT |", e)


round_no = 1
while True:
    do_rename = (round_no - 1) % 5 == 0
    title = renames[(round_no - 1) % len(renames)]
    max_threads = max(len(c["threads"]) for c in clients) if clients else 0

    for ti in range(max_threads):
        if do_rename:
            for c in clients:
                if ti >= len(c["threads"]):
                    continue
                tid = c["threads"][ti]
                change_title(
                    c["cl"],
                    build_headers(tid, c["csrftoken"]),
                    c["cookies"],
                    tid,
                    title
                )
            fixed_delay()

        for c in clients:
            if ti >= len(c["threads"]):
                continue
            tid = c["threads"][ti]
            text = random.choice(texts)
            send_msg(c["cl"], tid, text)

        fixed_delay()

    round_no += 1
