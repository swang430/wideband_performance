import { useEffect } from 'react';
import Editor, { useMonaco } from '@monaco-editor/react';
import { configureMonacoYaml } from 'monaco-yaml';
import { useTheme } from '../contexts/ThemeContext';
import { configSchema, scenarioSchema } from '../schemas/yamlSchemas';

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

    useEffect(() => {
        if (!monacoInstance) return;

        const isConfig = filename === 'config.yaml';
        const schema = isConfig ? configSchema : scenarioSchema;
        const schemaUri = isConfig
            ? 'inmemory://model/config-schema.json'
            : 'inmemory://model/scenario-schema.json';

        const dispose = configureMonacoYaml(monacoInstance, {
            validate: true,
            enableSchemaRequest: false,
            hover: true,
            completion: true,
            format: true,
            schemas: [
                {
                    uri: schemaUri,
                    fileMatch: [filename],
                    schema
                }
            ]
        });

        return () => {
            if (typeof dispose === 'function') {
                dispose();
            }
        };
    }, [monacoInstance, filename]);

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
                quickSuggestions: true,
                wordWrap: 'on',
                folding: true,
                lineNumbers: 'on',
                glyphMargin: false
            }}
        />
    );
}
