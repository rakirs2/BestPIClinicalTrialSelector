(() => {
    const STORAGE_KEY = "bestpi-theme";

    function applyTheme(rawValue) {
        if (!rawValue || rawValue === "system") {
            document.documentElement.removeAttribute("data-theme");
            return null;
        }

        document.documentElement.setAttribute("data-theme", rawValue);
        return rawValue;
    }

    function getPreference() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch {
            return null;
        }
    }

    function setPreference(value) {
        try {
            localStorage.setItem(STORAGE_KEY, value);
        } catch {
            /* ignore */
        }
    }

    function clearPreference() {
        try {
            localStorage.removeItem(STORAGE_KEY);
        } catch {
            /* ignore */
        }
    }

    const stored = getPreference();
    applyTheme(stored);

    window.bestpiTheme = {
        applyTheme(value) {
            applyTheme(value);
        },
        getPreference() {
            return getPreference();
        },
        setPreference(value) {
            setPreference(value);
            applyTheme(value);
        },
        clearPreference() {
            clearPreference();
            applyTheme(null);
        }
    };
})();
