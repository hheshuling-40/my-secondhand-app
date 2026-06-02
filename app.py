< !DOCTYPE
html >
< html
lang = "zh-TW" >
< head >
< meta
charset = "UTF-8" >
< meta
name = "viewport"
content = "width=device-width, initial-scale=1.0" >
< title > BLIND
BOX < / title >
< style >
/ *全域黑白灰極簡設定 * /
*{
    margin: 0;
padding: 0;
box - sizing: border - box;
font - family: -apple - system, BlinkMacSystemFont, "Segoe UI", Roboto, sans - serif;
}

body
{
    background - color:  # 121212;
        color:  # FFFFFF;
display: flex;
justify - content: center;
align - items: center;
min - height: 100
vh;
}

.container
{
    width: 100 %;
max - width: 400
px;
padding: 40
px
20
px;
text - align: center;
}

h1
{
    font - size: 1.5rem;
font - weight: 300;
letter - spacing: 4
px;
margin - bottom: 8
px;
color:  # EEEEEE;
}

.subtitle
{
    font - size: 0.85rem;
color:  # 777777;
letter - spacing: 2
px;
margin - bottom: 40
px;
}

/ *盲盒主視覺區 * /
.box - display
{
    width: 160px;
height: 160
px;
background:  # 1E1E1E;
border: 1
px
solid  # 333333;
margin: 0
auto
40
px
auto;
display: flex;
justify - content: center;
align - items: center;
position: relative;
transition: transform
0.5
s
ease;
}

.box - display.shake
{
    animation: shake 0.5s ease - in -out;
}

.box - icon
{
    font - size: 2.5rem;
color:  # 555555;
}

/ *價格與精簡按鈕 * /
.price - tag
{
    font - size: 1.2rem;
font - weight: 400;
color:  # AAAAAA;
margin - bottom: 20
px;
letter - spacing: 1
px;
}

.btn
{
    width: 100 %;
padding: 14
px;
background:  # FFFFFF;
color:  # 000000;
border: none;
font - size: 0.9
rem;
font - weight: 600;
letter - spacing: 2
px;
cursor: pointer;
transition: background
0.2
s, opacity
0.2
s;
}

.btn: hover
{
    background:  # CCCCCC;
}

/ *信用卡彈窗(Modal) * /
.modal - overlay
{
    position: fixed;
top: 0;
left: 0;
width: 100 %;
height: 100 %;
background: rgba(0, 0, 0, 0.85);
display: flex;
justify - content: center;
align - items: center;
opacity: 0;
pointer - events: none;
transition: opacity
0.3
s
ease;
z - index: 100;
}

.modal - overlay.active
{
    opacity: 1;
pointer - events: auto;
}

.modal
{
    background:  # 1A1A1A;
        border: 1
px
solid  # 333333;
width: 90 %;
max - width: 360
px;
padding: 30
px
24
px;
text - align: left;
}

.modal - title
{
    font - size: 1.1rem;
font - weight: 400;
letter - spacing: 1
px;
margin - bottom: 24
px;
color:  # DDDDDD;
text - align: center;
}

/ *精簡輸入框 * /
.form - group
{
    margin - bottom: 16px;
}

.form - group
label
{
    display: block;
font - size: 0.75
rem;
color:  # 777777;
margin - bottom: 6
px;
letter - spacing: 1
px;
}

.form - control
{
    width: 100 %;
padding: 10
px;
background:  # 242424;
border: 1
px
solid  # 333333;
color:  # FFFFFF;
font - size: 0.9
rem;
outline: none;
}

.form - control: focus
{
    border - color:  # 666666;
}

.form - row
{
    display: flex;
gap: 12
px;
}

/ *彈窗內精簡按鈕 * /
.modal - actions
{
    margin - top: 24px;
display: flex;
gap: 12
px;
}

.btn - secondary
{
    background: transparent;
color:  # 888888;
border: 1
px
solid  # 333333;
}

.btn - secondary: hover
{
    background:  # 222222;
        color:  # FFFFFF;
}

/ *動畫效果 * /


@keyframes


shake
{
    0 % {transform: translate(1px, 1px) rotate(0
deg);}
10 % {transform: translate(-1px, -2
px) rotate(-1
deg);}
20 % {transform: translate(-3px, 0
px) rotate(1
deg);}
30 % {transform: translate(0px, 2
px) rotate(0
deg);}
40 % {transform: translate(1px, -1
px) rotate(1
deg);}
50 % {transform: translate(-1px, 2
px) rotate(-1
deg);}
60 % {transform: translate(-3px, 1
px) rotate(0
deg);}
70 % {transform: translate(2px, 1
px) rotate(-2
deg);}
80 % {transform: translate(-1px, -1
px) rotate(1
deg);}
90 % {transform: translate(2px, 2
px) rotate(0
deg);}
100 % {transform: translate(1px, -2
px) rotate(-1
deg);}
}
< / style >
< / head >
< body >

< div


class ="container" >

< h1 > BLIND
BOX < / h1 >
< div


class ="subtitle" > 盲盒專區 < / div >

< div


class ="box-display" id="blindBox" >

< div


class ="box-icon" > ? < / div >

< / div >

< div


class ="price-tag" > $150 / 次 < / div >

< button


class ="btn" id="openPayBtn" > 購買 < / button >

< / div >

< div


class ="modal-overlay" id="payModal" >

< div


class ="modal" >

< div


class ="modal-title" > CREDIT CARD < / div >

< form
id = "paymentForm"
onsubmit = "handlePayment(event)" >
< div


class ="form-group" >

< label > 卡號 < / label >
< input
type = "text"


class ="form-control" placeholder="•••• •••• •••• ••••" maxlength="19" required >

< / div >

< div


class ="form-row" >

< div


class ="form-group" style="flex: 1;" >

< label > 到期日 < / label >
< input
type = "text"


class ="form-control" placeholder="MM/YY" maxlength="5" required >

< / div >
< div


class ="form-group" style="flex: 1;" >

< label > 安全碼 < / label >
< input
type = "text"


class ="form-control" placeholder="CVC" maxlength="3" required >

< / div >
< / div >

< div


class ="modal-actions" >

< button
type = "button"


class ="btn btn-secondary" id="closePayBtn" > 取消 < / button >

< button
type = "submit"


class ="btn" > 支付 $150 < / button >

< / div >
< / form >
< / div >
< / div >

< script >
// DOM
節點獲取
const
openPayBtn = document.getElementById('openPayBtn');
const
closePayBtn = document.getElementById('closePayBtn');
const
payModal = document.getElementById('payModal');
const
blindBox = document.getElementById('blindBox');

// 開啟支付彈窗
openPayBtn.addEventListener('click', () = > {
    payModal.classList.add('active');
});

// 關閉支付彈窗
closePayBtn.addEventListener('click', () = > {
    payModal.classList.remove('active');
});

// 處理支付與原有的盲盒動畫功能
function
handlePayment(event)
{
    event.preventDefault(); // 阻止表單預設提交行為

                               // 關閉支付彈窗
payModal.classList.remove('active');

// 觸發原有的盲盒搖晃與開獎功能
blindBox.classList.add('shake');

setTimeout(() = > {
    blindBox.classList.remove('shake');
alert('支付成功！盲盒已開啟。');
// 這裡可串接您原有的開獎邏輯(如顯示獲得的內容)
}, 1200);
}
< / script >
< / body >
< / html >