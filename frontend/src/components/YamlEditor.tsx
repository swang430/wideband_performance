import { useEffect } from 'react';
import Editor, { useMonaco } from '@monaco-editor/react';
import { useTheme } from '../contexts/ThemeContext';

interface YamlEditorProps {
    value: string;
    onChange: (value: string | undefined) => void;
    filename: string;
    readOnly?: boolean;
}

export default function YamlEditor({ value, onChange, filename, readOnly = false }: YamlEditorProps) {
    const { mode } = useTheme();
    const monacoInstance = useMonaco();

    // 监听主题变化并更新编辑器主题
    useEffect(() => {
        if (monacoInstance) {
            monacoInstance.editor.setTheme(mode === 'dark' ? 'vs-dark' : 'light');
        }
    }, [mode, monacoInstance]);

    return (
        <Editor
            height="100%"
            language="yaml"
            path={filename}
            theme={mode === 'dark' ? 'vs-dark' : 'light'}
            value={value}
            onChange={onChange}
            options={{
                minimap: { enabled: false },
                fontSize: 13,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                readOnly: readOnly,
                renderWhitespace: 'selection',
                tabSize: 2,
                wordWrap: 'on',
                folding: true,
                lineNumbers: 'on',
                glyphMargin: false
            }}
        />
    );
}
