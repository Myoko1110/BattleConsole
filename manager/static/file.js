let href = [];
const url = new URL(document.location);
const params = url.searchParams;
const path = params.get('p');
const source = params.get('s');
const cutsource = params.get('k');
const infos = params.get('i');
const info_success = document.getElementById('info_success');
const info_error = document.getElementById('info_error');
const copy = document.getElementById('copy');
const copysvg = document.getElementById('copysvg');
const cut = document.getElementById('cut');
const cutsvg = document.getElementById('cutsvg');
const del = document.getElementById('del');
const delsvg = document.getElementById('delsvg');
const paste = document.getElementById('paste');
const pastesvg = document.getElementById('pastesvg');
const edit = document.getElementById('edit');
const editsvg = document.getElementById('editsvg');
const rnm = document.getElementById('rnm');
const rnmsvg = document.getElementById('rnmsvg');
const confirm = document.getElementById('confirm');
const Delete = document.getElementById('delete');
const Rename = document.getElementById('rename');
const rename_box = document.getElementById('rename_box');
confirm.style.transform = 'scale(0, 0)';
copy.style.cursor = 'not-allowed';
del.style.cursor = 'not-allowed';
edit.style.cursor = 'not-allowed';
rnm.style.cursor = 'not-allowed';
copysvg.style.fill = '#a9a9a9';
delsvg.style.fill = '#a9a9a9';
editsvg.style.fill = '#a9a9a9';
rnmsvg.style.fill = '#a9a9a9';

var inside = false;

history.replaceState('', '', String(url).replace(/&i=.*/, ''));

// ファイル数の取得
let filenumber = $('#ul').attr('file');
$('#numberfile').text(filenumber + '個の項目');

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
async function success(info){
    (new URL(window.location.href)).searchParams.delete('i');
    info_success.style.display = 'flex';
    $('#info_success_h1').text(info[1]);
    $('.info').toggleClass('active');
    await sleep(3000);
    $('.info').toggleClass('active');
}
async function error(info){
    info_error.style.display = 'flex';
    $('#info_error_h1').text(info[1]);
    $('.info').toggleClass('active');
    await sleep(3000);
    $('.info').toggleClass('active');
}

if (infos !== null && infos !== ''){
    let info = infos.split(',');
    if (info[0] === 's'){
        success(info);
    }else{
        error(info);
    }
}

// 削除の確認
async function delete_file(){
    Delete.style.display = 'inline';
    await sleep(10);
    confirm.style.transform = 'scale(1, 1)';
    Delete.classList.toggle('active');
}

// 本削除
function delete_file_confirm(){
    let str = href.join(',');
    location.href='fd?p=' + str;
}

async function rename_file(){
    rename_box.value = $(`li[dir="${href[0]}"]`).attr('name');
    Rename.style.display = 'inline';
    await sleep(10);
    confirm.style.transform = 'scale(1, 1)';
    Rename.classList.toggle('active');
}

function rename_file_confirm(){
    if (path.endsWith('/')){
        to_name = `${path}${rename_box.value}`;
    }else{
        to_name = `${path}/${rename_box.value}`;
    }
    location.href = `fr?p=${href[0]}&d=${to_name}`;
}

async function inside_cancel(){
    inside = true;
    await sleep(101);
    inside = false;
}
// 削除キャンセル
async function cancel(t){
    if (inside === false){
        document.querySelector('.active').classList.toggle('active');
        await sleep(100);
        confirm.style.transform = 'scale(0, 0)';
        Delete.style.display = 'none';
        Rename.style.display = 'none';
    }
}
// ファイルコピー
function copy_file(){
    location.href = '?p=' + path + '&s=' + href.join(',');
}

// ファイル切り取り
function cut_file(){
    location.href = '?p=' + path + '&k=' + href.join(',');
}

// ファイル貼り付け
function paste_file(){
    if(source != null){
        location.href = './fc?s=' + source + '&d=' + path;
    }else{
        location.href = './fm?s=' + cutsource + '&d=' + path;
    }
}

// ファイル編集
function edit_file(){
    if(href.length !== 0){
        if ($('.selected').attr('filetype') === 'folder') {
            dir = '?p=' + $('.selected').attr('dir');
            location.href = dir;
        }else{
            dir = 'fe?p=' + $('.selected').attr('dir');
            location.href = dir;
        }
    }
}

// コピー元のソースを取得
if(source != null || cutsource != null){
    if(source != null){
        CopySource = '&s=' + source;
    }else{
        CopySource = '&k=' + cutsource;
        for (let i of cutsource.split(',')){
            try{
                document.querySelector(`li[dir="${i}"]`).querySelector('svg').style.fill = '#969696';
            }catch (e){
                continue
            }
        }
    }
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
        console.log(href);
    }else{
        href = href.filter(item => (item.match($(this).attr('dir'))) == null);
        console.log(href);
    }

    // 選択がないとき
    if(href.length === 0){
        copy.style.cursor = 'not-allowed';
        del.style.cursor = 'not-allowed';
        edit.style.cursor = 'not-allowed';
        rnm.style.cursor = 'not-allowed';
        copysvg.style.fill = '#a9a9a9';
        delsvg.style.fill = '#a9a9a9';
        editsvg.style.fill = '#a9a9a9';
        rnmsvg.style.fill = '#a9a9a9';
        del.setAttribute('onclick', '');
        copy.setAttribute('onclick', '');
        cut.setAttribute('onclick', '');
        edit.setAttribute('onclick', '');
        rnm.setAttribute('onclick', '');
        $('#selecting').removeClass('hidden');

    // 選択があるとき
    }else{
        copy.style.cursor = 'pointer';
        del.style.cursor = 'pointer';
        copysvg.style.fill = '#123767';
        cutsvg.style.fill = '#123767';
        delsvg.style.fill = '#123767';
        del.setAttribute('onclick', 'delete_file()');
        copy.setAttribute('onclick', 'copy_file()');
        cut.setAttribute('onclick', 'cut_file()');

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
    if(href.length === 1){
        rnm.style.cursor = 'pointer';
        rnm.setAttribute('onclick', 'rename_file()');
        rnmsvg.style.fill = '#123767';
    }else{
        rnm.style.cursor = 'not-allowed';
        rnmsvg.style.fill = '#a9a9a9';
        rnm.setAttribute('onclick', '');
    }
});

document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.key === 'c') {
        if(href.length !== 0){
            copy_file();
        }
    }

    if (event.ctrlKey && event.key === 'v') {
        if(source != null){
            paste_file();
        }
    }

    if (event.key === 'Enter') {
        if(getComputedStyle(Delete).display !== 'none'){
            delete_file_confirm();
            return;
        }
        if(getComputedStyle(Rename).display !== 'none'){
            rename_file_confirm();
            return;
        }
        if(href.length !== 0){
            if ($('.selected').attr('filetype') === 'folder') {
                dir = '?p=' + $('.selected').attr('dir');
                location.href = dir;
            }else{
                dir = 'fe?p=' + $('.selected').attr('dir');
                location.href = dir;
            }
        }
    }

    if (event.key === 'Delete') {
        if(getComputedStyle(Rename).display !== 'none'){
            return;
        }
        if(href.length !== 0){
            delete_file();
        }
    }
});
