const socket = io();
const url = new URL(window.location.href);
const form = document.querySelector('form');
const input = document.querySelector('input');
let server = url.searchParams.get('s');
const btn = document.getElementById(server);

btn.style.backgroundColor = '#1c58a6';
btn.style.color = '#ffffff';
btn.style.border = '2px #1c58a6 solid';


socket.on('console', function(cmd) {
    console.log('aa')
    if(server === 'proxy'){
        $('#console').html(cmd.proxy.replace(/\n/g, '<br>'));

    }else if(server === 'lobby'){
        $('#console').html(cmd.lobby.replace(/\n/g, '<br>'));

    }else if(server === 'main'){
            $('#console').html(cmd.main.replace(/\n/g, '<br>'));

    }else{
        $('#console').html('サーバーが不明です');

    }
})

input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        let cmd = document.getElementById('command').value;
        socket.emit('console', {'srv': server, 'cmd': cmd});
        document.getElementById('command').value = "";
    }
});
