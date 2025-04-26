import DOMPurify from "dompurify";
import { marked } from "marked";
export default function SystemResponse({ data, createdAt }) {
	const markdown = marked(data);
	const sanitized = DOMPurify.sanitize(markdown);
	return (
		<>
			<div
				className="text-xs mt-4 leading-5 text-gray-900 p-4 bg-white border-gray-200 rounded-md border-2"
				dangerouslySetInnerHTML={{ __html: sanitized }}
			/>
			<div className="text-gray-500 text-xs mt-1 mb-3">
				Generated {createdAt}
			</div>
		</>
	);
}
