import { useState, useEffect, useRef, ChangeEvent, FormEvent } from "react";
import SystemResponse from "./SystemResponse";

interface Message {
	role: string;
	date_created: string | null;
	content: string;
	data: string | null;
}

function App() {
	const bottomRef = useRef<HTMLDivElement>(null);
	const bottomRef1 = useRef<HTMLDivElement>(null);

	const [data, setData] = useState<Message[]>([]);
	const [input, setInput] = useState<string>("");

	const [loading, setLoading] = useState<Boolean>(false);

	const fetchData = async () => {
		try {
			let res = await fetch("http://127.0.0.1:8000/messages");
			if (!res.ok) {
				throw new Error(`HTTP error! status: ${res.status}`);
			}
			let data: Message[] = await res.json();
			setData(data);
			setLoading(false);
		} catch (error) {
			console.error("Failed to fetch data:", error);
		}
	};

	useEffect(() => {
		fetchData();
	}, []);

	const submitHandler = async (e: FormEvent<HTMLFormElement>) => {
		e.preventDefault();
		try {
			setLoading(true);
			const response = await fetch("http://127.0.0.1:8000/messages", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(input),
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}
			const newMessages: Message[] = await response.json();
			const newData: Message[] = [...data, ...newMessages];
			setData(newData);
			setLoading(false);
			setInput("");
		} catch (error) {
			console.error("Error:", error);
		}
	};

	const changeHandler = (e: ChangeEvent<HTMLTextAreaElement>) => {
		e.preventDefault();
		setInput(e.currentTarget.value);
	};

	useEffect(() => {
		if (bottomRef.current) {
			bottomRef.current.scrollIntoView({ behavior: "auto" });
		}
	}, [data, loading]);

	useEffect(() => {
		if (bottomRef1.current) {
			bottomRef1.current.scrollIntoView({ behavior: "auto" });
		}
	}, [data, loading]);

	return (
		<main className="h-screen w-full grid grid-cols-12 bg-[#EAE1E1]/50">
			{/* Chat */}
			<section className="m-4 pl-2 overflow-y-auto overflow-x-hidden flex flex-col shrink-0 bg-white flex-1 max-h-full col-span-4 border-gray-200 rounded-md border-2">
				<ul className="h-[80%] overflow-y-auto flex flex-col">
					{data &&
						data.map((msg: Message) => {
							if (msg.role === "user") {
								return (
									<li
										key={msg.date_created}
										className="text-sm max-w-4/5 p-2 rounded-lg m-2 bg-[#F5F5F5]/50 text-gray-700"
									>
										{msg.content}
									</li>
								);
							}
							if (msg.role === "system") {
								return (
									<li
										key={msg.date_created}
										className="text-sm font-light max-w-4/5 self-end p-2 rounded-lg shadow-md m-2 bg-[#DDDDC7]"
									>
										{msg.content}
									</li>
								);
							}
						})}
					{loading && (
						<div className="text-gray-400 text-xl animate-pulse">...</div>
					)}
					<div ref={bottomRef1} />
				</ul>
				<section>
					<form
						onSubmit={(e) => submitHandler(e)}
						className="flex flex-col w-full flex p-3 gap-2"
					>
						<textarea
							placeholder="How can I help you today?"
							className="border-2 text-sm border-gray-300 p-2"
							value={input}
							onChange={(e) => changeHandler(e)}
						/>
						<button
							disabled={input === ""}
							className="hover:bg-[#321D2F] bg-[#321D2F]/95 cursor-pointer  transition-all rounded-md text-white p-2"
							type="submit"
						>
							Submit
						</button>
					</form>
				</section>
			</section>

			{/* Generation */}
			<section className="flex-col p-4 rounded-md overflow-y-auto overflow-x-hidden col-span-8 flex flex-1">
				<ul>
					{data &&
						data.map((msg) => {
							if (msg.data) {
								return (
									<SystemResponse
										key={msg.date_created}
										data={msg.data}
										date_created={msg.date_created}
									/>
								);
							}
						})}
				</ul>
				{loading && (
					<div className="text-gray-400 animate-pulse">Loading...</div>
				)}
				<div ref={bottomRef} />
			</section>
		</main>
	);
}

export default App;
