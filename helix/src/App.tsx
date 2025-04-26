import { useState, useEffect, useRef } from "react";
import SystemResponse from "./SystemResponse";

function App() {
	const bottomRef = useRef<HTMLDivElement>(null);
	const bottomRef1 = useRef<HTMLDivElement>(null);

	const [data, setData] = useState([]);
	const [input, setInput] = useState("");

	const [loading, setLoading] = useState(false);

	const fetchData = async () => {
		try {
			let res = await fetch("http://127.0.0.1:8000/messages");
			if (!res.ok) {
				throw new Error(`HTTP error! status: ${res.status}`);
			}
			let d = await res.json();
			setData(d);
			setLoading(false);
		} catch (error) {
			console.error("Failed to fetch data:", error);
		}
	};
	console.log(data);
	useEffect(() => {
		fetchData();
	}, []);

	const submitHandler = async (e) => {
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
			const newMessages = await response.json();
			const newData = [...data, ...newMessages];
			setData(newData);
			setLoading(false);
			setInput("");
		} catch (error) {
			console.error("Error:", error);
		}
	};

	const changeHandler = (e) => {
		e.preventDefault();
		setInput(e.target.value);
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
			<section className="m-4 pl-2 overflow-y-auto overflow-x-hidden flex flex-col shrink-0 bg-white flex-1 max-h-full col-span-4 border-gray-300 rounded-md border-2">
				<ul className="h-[80%] overflow-y-auto flex flex-col">
					{data &&
						data.map((msg) => {
							if (msg.role === "user") {
								return (
									<li className="text-sm max-w-4/5 p-2 rounded-lg m-2 bg-[#EAE1E1]/50 text-gray-700">
										{msg.content}
									</li>
								);
							}
							if (msg.role === "system") {
								return (
									<li className="text-sm font-light max-w-4/5 self-end p-2 rounded-lg shadow-md m-2 bg-[#DDDDC7]">
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
							disabled={loading}
							className="border-2 text-sm border-gray-300 p-2"
							value={input}
							onChange={(e) => changeHandler(e)}
						/>
						<button
							disabled={input === ""}
							className="hover:bg-[#321D2F] cursor-pointer bg-[#3D2E4F] transition-all rounded-md text-white p-2"
							type="submit"
						>
							Submit
						</button>
					</form>
				</section>
			</section>

			{/* Data */}
			<section className="flex-col m-4 p-4 rounded-md overflow-y-auto overflow-x-hidden col-span-8 flex flex-1">
				<ul>
					{data &&
						data.map((msg) => {
							if (msg.data) {
								return (
									<SystemResponse
										data={msg.data}
										createdAt={msg.date_created}
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
