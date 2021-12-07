<kbd>
<br>
<br>

![paru-packages](https://socialify.git.ci/parutalker/paru-packages/image?description=1&font=KoHo&forks=1&issues=1&language=1&owner=1&pattern=Circuit%20Board&pulls=1&stargazers=1&theme=Dark)

</kbd>
<br>
<br>

### Use
**Setting up xbps-src**
<br>
Clone this repo & clone the void-packages repo from github.
```sh
git clone --depth 1 https://github.com/void-linux/void-packages
git clone --depth 1 https://github.com/parutalker/paru-packages
cp -r paru-packages/srcpkgs/* void-packages/srcpkgs/
```
Install the binary bootstrap
```sh
cd void-packages && ./xbps-src binary-bootstrap
```
**Building packages**
```sh
./xbps-src pkg <pkgname>
```
For more info on [building-packages](https://github.com/void-linux/void-packages#building-packages)<br><br>PR welcome!<br>Issues and request are welcome =)

## template-repo

 - abyss-packages : https://codeberg.org/mobinmob/abyss-packages
 - xanmod-kernel : https://notabug.org/Marcoapc/voidxanmodK
 - picom-ibhagwan : https://github.com/ibhagwan/picom-ibhagwan-template
 - Ungoogled Chromium : https://github.com/DAINRA/ungoogled-chromium-void