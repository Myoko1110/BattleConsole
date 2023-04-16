const textarea = document.getElementById("textarea");

textarea.addEventListener("keydown", function(e) {
    // Tabを押したらスペースを4つ代入する
    if (e.key === "Tab") {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        const value = this.value;
        this.value = value.substring(0, start) + "    " + value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
    }
    // Backspaceが押されたとき、前に4つスペースがあったらそれを削除
    if (e.key === "Backspace") {
        const start = this.selectionStart;
        const value = this.value;
            if (value.substring(start - 4, start) === "    ") {
                e.preventDefault();
                this.value = value.substring(0, start - 4) + value.substring(start);
                this.selectionStart = this.selectionEnd = start - 4;
            }
        }
});
