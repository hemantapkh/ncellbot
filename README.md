<p align="center">
<a href="https://github.com/hemantapkh/ncellbot/stargazers">
<img src="https://img.shields.io/github/stars/hemantapkh/ncellbot" alt="Stars">
</a>
<a href="https://github.com/hemantapkh/ncellbot/fork">
<img src="https://img.shields.io/github/forks/hemantapkh/ncellbot.svg" alt="Forks"/>
</a>
<img src="https://visitor-badge.laobi.icu/badge?page_id=hemantapkh.ncellbot" alt="visitors" />
<a href="https://github.com/hemantapkh/ncellbot/graphs/contributors">
<img src="https://img.shields.io/github/contributors/hemantapkh/ncellbot.svg" alt="Contributors" />
<a href="https://www.youtube.com/c/H9TechYouTube?sub_confirmation=1">
<img src="https://img.shields.io/badge/YouTube-H9-red" alt="Subscribe my channel H9"/>
</a>
</a>
</p>

<p align="center">
<img src="images/ncellbot.jpg" align="center" height=375 alt="Ncell Bot" />
</p>

<p align="center">
<a href="https://t.me/ncellappbot">
<img src='https://img.shields.io/badge/Telegram-Active-blue?style=for-the-badge&logo=telegram'>
</a>
<a href="https://m.me/ncellappbot">
<img src='https://img.shields.io/badge/Facebook-Inactive-red?style=for-the-badge&logo=facebook'>
</a>
</P>
<h2 align='center'>🤖 Ncell Chat Bot for Telegram</h2>

<p align="center">
Ncell bot is a free and open-source telegram bot to use the services of the Ncell App. You can use services like sending SMS, transferring balance, and many more which are not available in the official Ncell chatbot.
</P>

---

## ✔️ TODO

* Account sharing
* Balance transfer
* Call History
* Recharge history

---

## 🔐 Privacy

The bot is designed in a way to protect the privacy of users. You can learn more about this topic [here](https://telegra.ph/Privacy-On-Ncell-App-04-19).

---

## ⚙️ Deployment

<b>Currently, the latest version of [Ncell App](https://github.com/hemantapkh/ncellapp) is not open-sourced yet. I will try to release a new version as soon as possible.</b>

* Clone the repository, create a virtual environment, and install the requirements

    ```bash
    git clone https://github.com/hemantapkh/ncellbot && virtualenv ncellenv && source ncellenv/bin/activate && cd ncellbot && pip install -r requirements.txt
    ```

* Add your bot token in [config.json](config.json) file
* Run the [migration.py](migrations.py) file to open a database.

    ```python
    python migrations.py
    ```
* Now, start the bot polling

    ```python
    python telegrambot.py
    ```

---

## 🚀 Webhook Deployment

While polling and webhooks both accomplish the same task, webhooks are far more efficient. Polling sends a request for new events (specifically, Create, Retrieve, and Delete events, which signal changes in data) at a predetermined frequency and waits for the endpoint to respond whereas, webhooks only transfer data when there is new data to send, making them 100% efficient. That means that polling creates, on average, 66x more server load than webhooks. ([r](https://blog.cloud-elements.com/webhooks-vs-polling-youre-better-than-this))

- Generate an SSL certificate

    ```bash
    >> openssl genrsa -out sslPrivateKey.pem 2048
    >> openssl req -new -x509 -days 3650 -key sslPrivateKey.pem -out sslCertificate.pem
    ```

    *"Common Name (e.g. server FQDN or YOUR name)" should be your Host IP.*

- Edit [config.json](config.json) file and set

    - **connectionType** == **webhook**
    - **webhookHost** = **IP/Host where the bot is running**
    - **webhookPort** = **PORT (Need to be opened)**
    - **webhookListen** = **0.0.0.0** or **IP address in some VPS**
    - **sslCertificate** = **Directory of SSL certificate**
    - **sslPrivateKey** = **Directory of SSL private key**

* And, start the aioHttp server.

    ```python
    python telegrambot.py
    ```

---

## 🛺 Auto deployment on every push

You can set up GitHub actions to update the bot automatically on every push.

- Fork the repository on your GitHub account.

- Create a directory
    ```bash
    mkdir /opt/ncell
    ```

    *You should create a directory with the same name as above inside /opt, or edit the [deploy.yml](.github/workflows/deploy.yml) and [deployScript.sh](.github/workflows/deployScript.sh)*

- Create a virtual environment in the directory with name `ncellenv`

    ```bash
    virtualenv ncellenv
    ```

- Clone the repository and install the requirements in the virtual environment

    ```bash
    git clone https://github.com/hemantapkh/ncellbot && cd ncellbot && source /opt/ncell/ncellenv/bin/activate && pip install -r requirements.txt
    ```

- Create a database and move the database into `/opt/ncell`

    ```bash
    python migrations.py && mv database.sqlite /opt/ncell
    ```

- Generate SSH keys for your VPS and keep the private key in your GitHub secrets

    - Create the ssh key pair using the `ssh-keygen` command. You must leave the passphrase empty while generating the SSH key.
    - Copy and install the public ssh key on the server using `sh-copy-id -i your_public_key user@host` command.
    - Now, copy the content of the private key and paste it on your GitHub secrets with the name `SSHKEY`. *(Repository settings >> secrets >> New repository secret)*

- Create another GitHub secret with name `HOST` and save your Host IP.

- Edit [config.json](config.json) file and set

    - **database** = **/opt/ncell/database.sqlite**
    - **errorLog** =  **/opt/ncell/telegram.errors.logs**
    - If you are using webhooks, copy the SSL certificate and private key in `/opt/ncell` and set
        - **sslCertificate** == **/opt/ncell/sslCertificate.pem**
        - **sslPrivateKey** == **/opt/ncell/sslPrivateKey.pem**

- Copy the content of the edited config.json and save it on your repository secrets with name `CONFIG`. Don't forget to wrap the content of config file with single quotes like this `'Content of config.json'`.

- And, start the bot.

    ```bash
    source /opt/ncell/ncellenv/bin/activate && screen -dm python /opt/ncell/ncellbot/telegrambot.py
    ```

Now, every time you push on the `main` branch, the bot automatically gets updated.

---

## 💚 Contributing

Any contributions you make are **greatly appreciated**.

For minor fix, you can directly create a pull request and for adding a new feature, let's first discuss it in our [telegram group](https://t.me/h9discussion) or in [GitHub Discussion](https://github.com/hemantapkh/ncellbot/discussions).

---

## 🔑 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

-----
Made using [Ncell App](https://github.com/hemantapkh/ncellapp) and [pyTelegramBotApi](https://github.com/eternnoir/pyTelegramBotAPI) in Python💙 by [Hemanta Pokharel](https://github.com/hemantapkh/) [[✉️](mailto:hemantapkh@yahoo.com) [💬](https://t.me/hemantapkh) [📺](https://youtube.com/h9youtube)]