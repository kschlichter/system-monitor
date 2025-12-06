# system-monitor
This is how I monitor my server and remote desktops.  It won't work for you; don't bother.  It's only about 90% of what you need anyway and it will take a significant amount of effort on your part.  It's not a magic button that will instantly work, which is why it isn't in HACs.  

* The `hass_monitor.py' script sits in `~/.hass_monitor/` and runs every 15 minutes and at reboot in a root crontab:
  *   ```
      # m h  dom mon dow   command
       */15 *  *   *   *   sudo python3 /home/kschlichter/.hass_monitor/hass_monitor.py
       @reboot             sudo python3 /home/kschlichter/.hass_monitor/hass_monitor.py
      ```
* The output file will be located in the directiory defined in the `file_paths` dictionary, near the top of the script, which I'll translate to a runtime parameter at some point.  If you aren't sure how to do this, you should give up now.
  * ```
    file_paths = {
    'schlerver': '/home/kschlichter/.hass_monitor/',
    'klaptop': '/home/kschlichter/.hass_monitor/',
    'koldstorage': '/home/kschlichter/.hass_monitor/'
    }
    ```
* The name of the file will be `hass_monitor_HOSTNAME.json`.  I've included `hass_monitor_schlerver.json` in this repository as an example.
* If the script is running on the same system as Home Assistant, you can mount the directory containing the output file into the Home Assistant Docker container in your `docker-compose.yml`
  *    ```
       hass:
         image: ghcr.io/home-assistant/home-assistant:2025.12.0
         container_name: hass
         volumes:
           - "/home/kschlichter/.hass_monitor:/config/www/hass_monitor/schlerver"  ### same system
           - "/mnt/storage/nextcloud/data/kschlichter/files/Home\ Assistant:/config/www/hass_monitor"  ### nextcloud directory with subdirectories for all of my systems
       ```
  * If you're not using docker compose, you're running Hass OS, or doing something else, you can figure it out.  Your mom believes in you, I'm sure.
* If the script is monitoring a different system, I use [nextcloud](https://nextcloud.com/) to get it sync'd back to the server into a `Home Assistant` that has a directory for each system I monitor.
  * Incidentally, when I need to make a change, I can do that in nextcloud and let it sync out to each system, instead of logging into them individually.
* I use the [RESTful Sensors](https://www.home-assistant.io/integrations/sensor.rest/) integration to generate sensors from the `.json` files.
  * I have [split up my](https://www.home-assistant.io/docs/configuration/splitting_configuration/) `configuration.yaml`.  If you didn't, I'll pray for you.
  * In my hass directory, I have a `rest-sensors` directory containing a file for each system I monitor (e.g. the `schlerver.yaml`) I've included in this repository.
    * You'll have to make a lot of modifications before it'll work for you but it should mostly be find and replace.  If you can't figure out something, remember that I told you it wouldn't work and you shouldn't've bothered.
* Each system also has a series of other template sensors associated.  These are mostly derivitives of the RESTful sensors but some are from other integrations.
  * I've included `sensor.yaml` in the repo as an example.  Find and replace to modify it for your needs.
  * Again, since I've split up my configuration, this resides under `templates/sensor.yaml` next to files like `templates/binary_sensor.yaml` and `templates/trigger_sensor.yaml`.  That's probably not what you've done, so you'll have to figure it out from here.
* Examples of my [alerts](https://www.home-assistant.io/integrations/alert/) can be found in the `alert.yaml` file in this repo.
* My `lovelace_summary_card` is a series of [glance cards](https://www.home-assistant.io/dashboards/glance/) in a [vertical stack card](https://www.home-assistant.io/dashboards/vertical-stack/).  That gives me something like:
  * <img width="580" height="965" alt="image" src="https://github.com/user-attachments/assets/7c93e864-281b-4988-9294-ac8142d006a1" />
  * Clicking on the summary icon links to a dashboard for that system.  I've included the `lovelace_dashboard` yaml in the repository, which gives me something like:
    * <img width="1207" height="1539" alt="image" src="https://github.com/user-attachments/assets/0d8a5ef6-769c-45eb-ba35-f26b3301a595" />

    * It's a lot; I know.
* My system-specific dashboards use YAML similar to `schlerver_dashboard` with some things removed (i.e. they don't have a GPU or RAID).
* Finally, I have a series of sensors that I use to set [input booleans](https://www.home-assistant.io/integrations/input_boolean/), and leverage in some automations (i.e. analysing drive info and deciding whether the RAID is healthy in order to trigger the alert).  I've included some of that in this repository but there are pieces you'll have to figure out on your own.  Partly, that's because I'm too lazy to track them down, and partly it's because it's just not that hard.

