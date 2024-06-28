# Mio3 Bones

ボーン編集用のサポートツール

## 導入方法

[Code > Download ZIP](https://github.com/mio3io/Mio3Bones/archive/master.zip) から ZIP ファイルをダウンロードします。
Blender の `Edit > Preferences > Addons > Install` を開き、ダウンロードしたアドオンの ZIP ファイルを選択してインストールボタンを押します。インストール後、該当するアドオンの左側についているチェックボックスを ON にします。

## 機能

右クリックメニューと、アーマチュアのメニューに追加されます

### アーマチュア＞トランスフォーム

-   ボーンを均等にする
-   ボーンを整列する（先頭と末端ボーンを基準）

### アーマチュア＞名前

-   ボーンに通し番号をふる

### サイドバー＞ Mio3 タブ

-   ボーン名のフォーマットの一括変換（実験的）ポーズモードで表示されているボーンを任意のフォーマットに変換

実験的に追加しています。うまく変換されるかわからないため変換後に確認してください。

元の名前が一定のパターンにあてはまるものでないとうまく変換されないことがあります。
表示されているものだけを変換する仕様になっているため、必要な部分のみ変換してください。

認識されるパターン例

-   UpperArm_L
-   Upper Arm_L
-   Upper_Arm_L
-   UpperArm.L
-   Upper Arm.L
-   Upper_Arm.L
-   L_UpperArm
-   Hair.001
-   Hair_L.001
-   Hair.L.001

認識されないパターン

-   Left/Right のような LR 以外のサフィックス

正常に変換されないパターン

-   IK_Arm_L のような大文字パターンは I と K は分離され I_K_Arm_L のように扱われます

認識されないパターンの場合、「編集」＞「名前を一括変換」＞「ボーン」を使って可能な範囲で認識されるパターンになるように変換しておくとよいでしょう。

#### ToDo

AvatarName_ / Twist_ / Support_ / Hair_ などのカスタムプレフィックスへの対応
