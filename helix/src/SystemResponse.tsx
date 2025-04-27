import { useState } from "react";

export default function SystemResponse({
	data,
	date_created,
}: {
	data: string;
	date_created: string | null;
}) {
	const [text, setText] = useState<string>(data);

	return (
		<>
			<textarea
				className="w-full p-2 bg-white/70 hover:bg-white min-h-[400px] text-sm"
				onChange={(e) => setText(e.currentTarget.value)}
				value={text}
			/>
			<div className="text-gray-500 text-xs mt-1 mb-3">
				Generated on {date_created}
			</div>
		</>
	);
}
