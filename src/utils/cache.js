const cache = {
    setVal(key, val) {
        let newVal = typeof val === 'object' ? JSON.stringify(val) : val
        localStorage.setItem(key, newVal)
    },
    getVal(key) {
        const newVal = localStorage.getItem(key)
        try {
            return typeof newVal === 'object' ? JSON.parse(newVal) : newVal
        } catch {
            return newVal;
        }
    },
    removeVal(key) {
        localStorage.removeItem(key)
    },
    clearVal() {
        localStorage.clear()
    }
}
export default cache;
