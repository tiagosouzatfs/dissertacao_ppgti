# Dissertação PPgTI

Repositório criado para armazenar os arquivos da dissertação do PPgTI

- **Requirements**:
    * Host: SO Windows 11 Pro 24H2
        - Windows: https://www.microsoft.com/pt-br/software-download/windows11
    * Virtualbox: VirtualBox 7.1.4
        - Virtualbox: https://www.virtualbox.org/wiki/Download_Old_Builds_7_1
        - CPU: 4
        - RAM: 8GB
        - Storage: 40GB 
    * Guest: SO Ubuntu 20.04.6 LTS (Focal Fossa)
        - Ubuntu: https://releases.ubuntu.com/focal/
        - User: **vboxuser** / password: **123456789**
        - you need to install the **git** package before installing Containernet: 
            * `sudo apt-get update && sudo apt-get install git -y`
    * Install Containernet, which already includes Mininet-WiFi:
        - Follow the steps to install Containernet according to the repository below
        - Containernet: https://github.com/ramonfontes/containernet
    * Install VSCode
        Instaled using snap
    * Install WireShark
        Instaled using snap
