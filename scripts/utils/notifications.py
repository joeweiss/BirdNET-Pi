import apprise
import os
import socket
import sqlite3
from datetime import datetime

userDir = os.path.expanduser("~")
APPRISE_CONFIG = userDir + "/BirdNET-Pi/apprise.txt"
DB_PATH = userDir + "/BirdNET-Pi/scripts/birds.db"


def notify(body, title):
    apobj = apprise.Apprise()
    config = apprise.AppriseConfig()
    config.add(APPRISE_CONFIG)
    apobj.add(config)
    apobj.notify(
        body=body,
        title=title,
    )


def return_templated_string(
    template_string,
    species="",
    confidence="",
    date="",
    time="",
    week="",
    latitude="",
    longitude="",
    cutoff="",
    sens="",
    overlap="",
    listen_url="",
):
    sciName, comName = species.split("_")

    return (
        template_string.replace("$sciname", sciName)
        .replace("$comname", comName)
        .replace("$confidence", confidence)
        .replace("$listenurl", listen_url)
        .replace("$date", date)
        .replace("$time", time)
        .replace("$week", week)
        .replace("$latitude", latitude)
        .replace("$longitude", longitude)
        .replace("$cutoff", cutoff)
        .replace("$sens", sens)
        .replace("$overlap", overlap)
    )


def sendAppriseNotifications(
    species="",
    confidence="",
    path="",
    date="",
    time="",
    week="",
    latitude="",
    longitude="",
    cutoff="",
    sens="",
    overlap="",
    settings_dict={},
    db_path=DB_PATH,
):
    # print(sendAppriseNotifications)
    # print(settings_dict)
    if os.path.exists(APPRISE_CONFIG) and os.path.getsize(APPRISE_CONFIG) > 0:

        title = settings_dict.get("APPRISE_NOTIFICATION_TITLE")
        body = settings_dict.get("APPRISE_NOTIFICATION_BODY")
        sciName, comName = species.split("_")

        try:
            websiteurl = settings_dict.get("BIRDNETPI_URL")
            if len(websiteurl) == 0:
                raise ValueError("Blank URL")
        except Exception:
            websiteurl = "http://" + socket.gethostname() + ".local"

        listenurl = websiteurl + "?filename=" + path

        base_notify_body = return_templated_string(
            body,
            species=species,
            confidence=confidence,
            date=date,
            time=time,
            week=week,
            latitude=latitude,
            longitude=longitude,
            cutoff=cutoff,
            sens=sens,
            overlap=overlap,
            listen_url=listenurl,
        )

        base_notify_title = return_templated_string(
            title,
            species=species,
            confidence=confidence,
            date=date,
            time=time,
            week=week,
            latitude=latitude,
            longitude=longitude,
            cutoff=cutoff,
            sens=sens,
            overlap=overlap,
            listen_url=listenurl,
        )

        if settings_dict.get("APPRISE_NOTIFY_EACH_DETECTION") == "1":
            notify_body = base_notify_body
            notify_title = base_notify_title
            notify(notify_body, notify_title)

        APPRISE_NOTIFICATION_NEW_SPECIES_DAILY_COUNT_LIMIT = (
            1  # Notifies the first N per day.
        )
        if settings_dict.get("APPRISE_NOTIFY_NEW_SPECIES_EACH_DAY") == "1":
            try:
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                today = datetime.now().strftime("%Y-%m-%d")
                cur.execute(
                    f"SELECT DISTINCT(Com_Name), COUNT(Com_Name) FROM detections WHERE Date = DATE('{today}') GROUP BY Com_Name"
                )
                known_species = cur.fetchall()
                detections = [
                    d[1] for d in known_species if d[0] == comName.replace("'", "")
                ]
                numberDetections = 0
                if len(detections):
                    numberDetections = detections[0]
                if (
                    numberDetections > 0
                    and numberDetections
                    <= APPRISE_NOTIFICATION_NEW_SPECIES_DAILY_COUNT_LIMIT
                ):
                    notify_body = base_notify_body + " (first time today)"
                    notify_title = base_notify_title + " (first time today)"
                    notify(notify_body, notify_title)
                con.close()
            except sqlite3.Error as e:
                print(e)
                print("Database busy")
                time.sleep(2)

        if settings_dict.get("APPRISE_NOTIFY_NEW_SPECIES") == "1":
            try:
                con = sqlite3.connect(db_path)
                cur = con.cursor()
                today = datetime.now().strftime("%Y-%m-%d")
                cur.execute(
                    f"SELECT DISTINCT(Com_Name), COUNT(Com_Name) FROM detections WHERE Date >= DATE('{today}', '-7 day') GROUP BY Com_Name"
                )
                known_species = cur.fetchall()
                detections = [
                    d[1] for d in known_species if d[0] == comName.replace("'", "")
                ]
                numberDetections = 0
                if len(detections):
                    numberDetections = detections[0]
                if numberDetections > 0 and numberDetections <= 5:
                    notify_body = (
                        base_notify_body
                        + " (only seen "
                        + str(int(numberDetections))
                        + " times in last 7d)"
                    )
                    notify_title = (
                        base_notify_title
                        + " (only seen "
                        + str(int(numberDetections))
                        + " times in last 7d)"
                    )
                    notify(notify_body, notify_title)
                con.close()
            except sqlite3.Error:
                print("Database busy")
                time.sleep(2)


if __name__ == "__main__":
    print("notfications")
