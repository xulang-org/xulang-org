# Xu 品牌资源

本目录保存 Xu 的标识源文件，以及浅色、深色、办公和周边应用版本。

| 文件 | 用途 |
| --- | --- |
| `xu_classic.svg` | 内容标识、网站标识和 favicon |
| `xu_app_logo.svg` | 桌面应用、Dock、托盘和窗口图标 |
| `xu_app_icon.svg` | 桌面标识的兼容别名 |

官网实际使用 [`www/xu_classic.svg`](../www/xu_classic.svg)。更新标识时修改对应
SVG 源文件，再同步网站资源：

```sh
cp brand/xu_classic.svg www/xu_classic.svg
```

需要更新 PNG 导出时，使用 `rsvg-convert`：

```sh
rsvg-convert -w 512 -h 512 brand/xu_classic.svg -o brand/xu_classic.png
rsvg-convert -w 512 -h 512 brand/xu_app_logo.svg -o brand/xu_app_logo.png
cp brand/xu_app_logo.svg brand/xu_app_icon.svg
cp brand/xu_app_logo.png brand/xu_app_icon.png
```

图像导出只用于维护品牌资源，官网构建不依赖该工具。
