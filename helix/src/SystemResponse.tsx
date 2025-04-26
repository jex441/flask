import DOMPurify from "dompurify";
import { marked } from "marked";
export default function SystemResponse({ data }) {
	const markdown = marked(data);
	const sanitized = DOMPurify.sanitize(markdown);
	console.log(data);
	return (
		<div
			className="text-sm my-2 bg-white border-gray-200 p-2 rounded-md border-2"
			dangerouslySetInnerHTML={{ __html: sanitized }}
		/>
	);
}
