let href = []
const params = (new URL(document.location)).searchParams;
const path = params.get('p');
const source = params.get('s');
const copy = document.getElementById('copy');
const del = document.getElementById('del');
const copysvg = document.getElementById('copysvg');
const delsvg = document.getElementById('delsvg');
const confirm = document.getElementById('confirm');
const Delete = document.querySelector('.confirm_box');
const paste = document.getElementById('paste');
const pastesvg = document.getElementById('pastesvg');
const edit = document.getElementById('edit');
const editsvg = document.getElementById('editsvg');
confirm.style.transform = 'scale(0, 0)';
copy.style.cursor = 'not-allowed';
del.style.cursor = 'not-allowed';
edit.style.cursor = 'not-allowed';
copysvg.style.fill = '#a9a9a9';
delsvg.style.fill = '#a9a9a9';
editsvg.style.fill = '#a9a9a9';

// ファイル数の取得
let filenumber = $('#ul').attr('file')
console.log(filenumber)
$('#numberfile').text(filenumber + '個の項目')

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 削除の確認
function delete_file(){
    confirm.style.transform = 'scale(1, 1)';
    Delete.classList.toggle('active');
}

// 本削除
function delete_file_confirm(){
    let str = href.join(',');
    location.href='fd?p=' + str;
}

// 削除キャンセル
async function cancel(){
    Delete.classList.toggle('active');
    await sleep(100);
    confirm.style.transform = 'scale(0, 0)';
}
// ファイルコピー
function copy_file(){
    location.href = '?p=' + path + '&s=' + href.join(',');
}

// ファイル貼り付け
function paste_file(){
    location.href = './fc?s=' + source + '&d=' + path;
}

// ファイル編集
function edit_file(){
    if(href.length !== 0){
        if ($('.selected').attr('filetype') === 'folder') {
            dir = '?p=' + $('.selected').attr('dir')
            location.href = dir
        }else{
            dir = 'fe?p=' + $('.selected').attr('dir')
            location.href = dir
        }
    }
}

// コピー元のソースを取得
if(source != null){
    CopySource = '&s=' + source;
    paste.style.cursor = 'pointer';
    pastesvg.style.fill = '#123767';
    paste.setAttribute('onclick', 'paste_file()');
}else{
    paste.style.cursor = 'not-allowed';
    pastesvg.style.fill = '#a9a9a9';
    paste.setAttribute('onclick', '');
}

// ファイルを選択したらsubmitさせる
$(function () {
    $("#file").change(function () {
        $(this).closest("form").submit();
    });
});

// liをクリックしたとき
$('li').click(function() {

    // selectedクラスをつける
    $(this).toggleClass('selected');

    // 選択されたファイルを配列に追加/削除
    if(href.includes($(this).attr('dir')) === false){
        href.push($(this).attr('dir'));
        console.log(href)
    }else{
        href = href.filter(item => (item.match($(this).attr('dir'))) == null);
        console.log(href)
    }

    // 選択がないとき
    if(href.length === 0){
        copy.style.cursor = 'not-allowed';
        del.style.cursor = 'not-allowed';
        edit.style.cursor = 'not-allowed';
        copysvg.style.fill = '#a9a9a9';
        delsvg.style.fill = '#a9a9a9';
        editsvg.style.fill = '#a9a9a9';
        del.setAttribute('onclick', '');
        copy.setAttribute('onclick', '');
        edit.setAttribute('onclick', '');
        $('#selecting').removeClass('hidden');

    // 選択があるとき
    }else{
        copy.style.cursor = 'pointer';
        del.style.cursor = 'pointer';
        copysvg.style.fill = '#123767';
        delsvg.style.fill = '#123767';
        del.setAttribute('onclick', 'delete_file()');
        copy.setAttribute('onclick', 'copy_file()');

        console.log($('.selected').attr('filetype'))
        // 選択したものがファイルだったら
        if ($('.selected').attr('filetype') !== 'folder') {
            edit.style.cursor = 'pointer';
            editsvg.style.fill = '#123767';
            edit.setAttribute('onclick', 'edit_file()');
        }else{
            edit.style.cursor = 'not-allowed'
            editsvg.style.fill = '#a9a9a9';
            edit.setAttribute('onclick', '');
        }
        $('#selecting').addClass('hidden');
        $('#selecting-number').text(href.length);
    }
});

document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.key === 'c') {
        if(href.length !== 0){
            copy_file()
        }
    }

    if (event.ctrlKey && event.key === 'v') {
        if(source != null){
            paste_file()
        }
    }

    if (event.key === 'Enter') {
        if(href.length !== 0){
            if ($('.selected').attr('filetype') === 'folder') {
                dir = '?p=' + $('.selected').attr('dir')
                location.href = dir
            }else{
                dir = 'fe?p=' + $('.selected').attr('dir')
                location.href = dir
            }
        }
    }

    if (event.key === 'Delete') {
        if(href.length !== 0){
            delete_file()
        }
    }
});
