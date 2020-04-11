//@ts-check
// Note: This file is almost direct translation of lispish.py
// It skips the runtime since code won't be run on the client.
// Ideally this would be a module, but that's blocked on https://github.com/CTFd/CTFd/issues/1304

/** @param {number} size */
function getIndent(size) {
    return '    '.repeat(size)
}

class LispIshParseError extends Error {
    /**
     * @param {string} message
     * @param {number} line
     * @param {number} col
     */
    constructor(message, line, col) {
        super(message)
        this.line = line
        this.col = col
    }

    toString() {
        return `${this.message} at ${this.line}:${this.col}`
    }
}

const NAME_CHARS = new Set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ<=>/+-')

class LispIshValue {
    /**
     * @param {number} indent
     * @returns {string}
     */
    emit(indent) {
        throw new Error('Not implemented')
    }
    // No evaluate function!
}

class LispIshNumber extends LispIshValue {
    /** @param {number} value */
    constructor(value) {
        super()
        this.value = value
    }

    emit(indent = 0) {
        return `${getIndent(indent)}${this.value}`
    }
}

class LispIshString extends LispIshValue {
    /** @param {string} value */
    constructor(value) {
        super()
        this.value = value
    }

    emit(indent = 0) {
        return getIndent(indent) + JSON.stringify(this.value)
    }
}

class LispIshMethod extends LispIshValue {
    /**
     * @param {string} name
     * @param {LispIshValue[]} args
     */
    constructor(name, args) {
        super()
        this.name = name
        this.canonical_name = name.toUpperCase()
        this.args = args
    }

    /** @param {string} name */
    rename(name) {
        this.name = name
        this.canonical_name = name.toUpperCase()
    }

    emit(indent = 0) {
        if (this.args.length === 0) {
            return getIndent(indent) + `(${this.name})`
        }
        if (this.args.length === 1) {
            return getIndent(indent) + `(${this.name} ${this.args[0].emit(indent).trimLeft()})`
        }
        return [
            getIndent(indent) + `(${this.name}`,
            ...this.args.slice(0, -1)
                .map(arg => arg.emit(indent + 1)),
            `${this.args[this.args.length - 1].emit(indent + 1)})`
        ].join('\n')
    }
}

class LispIsh {
    constructor() {
        this.text = ''
        this.index = 0
        this.line = 1
        this.col = 0
    }

    /** @param {string} text */
    parse(text) {
        this.text = text
        this.index = this.col = 0
        this.line = 1
        const method = this._parse_method()
        this._consume_ws()
        this._expect_eof()
        return method
    }

    /**
     * @param {string} message
     * @private
     */
    _die(message) {
        throw new LispIshParseError(message, this.line, this.col)
    }

    _peek() {
        if (this.index == this.text.length) {
            this._die("Ran off end of input")
        }
        return this.text[this.index]
    }

    _eof() {
        return this.index === this.text.length
    }

    _consume() {
        if (this._peek() === '\n') {
            this.line += 1
            this.col = 0
        } else {
            this.col += 1
        }
        this.index += 1
        return this.text[this.index - 1]
    }

    /** @param {string} text */
    _expect(text) {
        if (this._peek() !== text) {
            this._die(`Expected <${text}> but found <${this._peek()}>`)
        }
        return this._consume()
    }

    _expect_eof() {
        if (!this._eof()) {
            this._die(`Expected <EOF> but found <${this._peek()}>`)
        }
    }

    _consume_ws() {
        while (!this._eof() && ' \t\r\n'.includes(this._peek())) {
            this._consume()
        }
    }

    _parse_method() {
        this._consume_ws()
        this._expect('(')
        const name = this._parse_name()
        const args = this._parse_args()
        this._consume_ws()
        this._expect(')')
        return new LispIshMethod(name, args)
    }

    _parse_name() {
        this._consume_ws()
        const name = []
        while (NAME_CHARS.has(this._peek())) {
            name.push(this._consume())
        }
        if (!name.length) {
            this._die(`Expected a name but found <${this._peek()}>`)
        }
        return name.join('')
    }

    _parse_args() {
        /** @type {LispIshValue[]} */
        const args = []
        this._consume_ws()
        while (this._peek() !== ')') {
            if (this._peek() === '(') {
                args.push(this._parse_method())
            } else if ('1234567890'.includes(this._peek())) {
                args.push(this._parse_int())
            } else if ('"\''.includes(this._peek())) {
                args.push(this._parse_str())
            } else {
                this._die(`Expected a string, number, or function call but got <${this._peek()}>`)
            }
            this._consume_ws()
        }
        return args
    }

    _parse_int() {
        this._consume_ws()
        /** @type {string[]} */
        const data = []
        while ('1234567890'.includes(this._peek())) {
            data.push(this._consume())
        }
        if (!data.length) {
            this._die(`Expected a number but got <${this._peek()}>`)
        }
        return new LispIshNumber(parseInt(data.join(''), 10))
    }

    _parse_str() {
        this._consume_ws()
        /** @type {string[]} */
        const data = []
        let escaped = false
        if ('"\''.includes(this._peek())) {
            var end = this._consume()
        } else {
            this._die(`Expected the start of a string but got <${this._peek()}>`)
        }

        while (escaped || this._eof() || this._peek() !== end) {
            if (this._eof()) {
                this._die('Unclosed string ran off end of input')
            }
            if (this._peek() === '\\') {
                this._consume()
                if (escaped) {
                    data.push('\\')
                }
                escaped = !escaped
                continue
            }
            data.push(this._consume())
            escaped = false
        }
        this._consume()
        return new LispIshString(data.join(''))
    }
}
